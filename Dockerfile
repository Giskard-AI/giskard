
FROM python:3.10 AS base-python
ARG RUN_TESTS=false

WORKDIR /app
# Install PDM
RUN curl -sSL https://pdm.fming.dev/install-pdm.py | python3 -
ENV PATH /root/.local/bin:$PATH
# Install virtualenv and create one
RUN pip3 install virtualenv && python3 -m virtualenv /app/python-client/.venv-prod

COPY python-client python-client
WORKDIR /app/python-client
RUN pdm run clean 

FROM base-python AS build-python
RUN pdm build 
# Create an environment and install giskard wheel. Some dependencies may require gcc which is only installed in build
# stage, but not in the production one
RUN WHEEL=$(ls dist/giskard*.whl) && .venv-prod/bin/pip install $WHEEL\[server\]

FROM build-python AS test-python
# TODO(Bazire): have a complete pass over deps to ensure what is where
RUN pdm install -G :all
RUN pdm run test

FROM eclipse-temurin:17-jdk-jammy as build-back-front
ARG FRONTEND_ENV=production

ENV _JAVA_OPTIONS="-Xmx4048m -Xms512m" \
    SPRING_PROFILES_ACTIVE=prod \
    MANAGEMENT_METRICS_EXPORT_PROMETHEUS_ENABLED=false \
    VUE_APP_ENV=${FRONTEND_ENV} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app
# unnecessary files are filtered out by .dockerignore
COPY frontend frontend
COPY backend backend
COPY gradle gradle
# Copying .git to make gradle-git-properties gradle plugin work
COPY .git .git

COPY build.gradle.kts gradle.properties gradlew settings.gradle.kts ./
RUN ./gradlew :backend:compileJava -Pprod --info --stacktrace --no-parallel

FROM build-back-front as build-backend
# Source : https://snyk.io/fr/blog/jlink-create-docker-images-spring-boot-java/
# Build package
RUN ./gradlew :backend:package -Pprod --info --stacktrace --no-parallel
# Unpack it
RUN jar xf ./backend/build/libs/backend*.jar
# Analyse java deps
RUN jdeps --ignore-missing-deps -q  \
    --recursive  \
    --multi-release 17  \
    --print-module-deps  \
    --class-path 'BOOT-INF/lib/*'  \
    ./backend/build/libs/backend*.jar > deps.info
# Build custom JRE
RUN jlink \
    --add-modules $(cat deps.info) \
    --strip-debug \
    --compress 2 \
    --no-header-files \
    --no-man-pages \
    --output /giskard-jre

FROM build-back-front as build-frontend
RUN ./gradlew :frontend:package -Pprod --info --stacktrace --no-parallel

FROM python:3.10-slim-bookworm as prod
ARG GISKARD_UID=50000

ENV SPRING_PROFILES_ACTIVE=prod
ARG DEBIAN_FRONTEND=noninteractive
ARG POSTGRES_VERSION=13
ARG SUPERVISOR_VERSION=4.2.5

ENV SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/postgres \
    SPRING_LIQUIBASE_URL=jdbc:postgresql://localhost:5432/postgres \
    GSK_HOST=0.0.0.0 \
    GSK_USER_HOME=/home/giskard \
    GSK_HOME=/home/giskard/datadir \
    GSK_DIST_PATH=/opt/giskard

ENV VENV_PATH=$GSK_DIST_PATH/internal-mlworker-venv

ENV PATH="$VENV_PATH/bin:/usr/lib/postgresql/${POSTGRES_VERSION}/bin:$PATH" \
    PGDATA=$GSK_HOME/database \
    GISKARD_HOME=$GSK_HOME

WORKDIR $GSK_DIST_PATH

RUN adduser --gecos "First Last,RoomNumber,WorkPhone,HomePhone" --disabled-password \
       --quiet "giskard" --uid "${GISKARD_UID}" --gid "0" --home "${GSK_USER_HOME}" && \
    mkdir -p "${GSK_HOME}/run" && chown -R "giskard:0" "${GSK_USER_HOME}" "${GSK_DIST_PATH}"

# https://www.postgresql.org/download/linux/debian/
# wget gnupg only for installation
# nginx to run frontend
# gettext-base to have envsubst
# git is neededby worker
RUN apt-get update && \
    apt-get -y install --no-install-recommends wget gnupg nginx gettext-base git \
    && sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list'\
    && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -\
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-${POSTGRES_VERSION} \
    && apt autoremove -y --purge wget gnupg \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Installing as a pip package, to avoid installing another version of python
RUN pip3 install "supervisor==${SUPERVISOR_VERSION}"

# # NOTE(Bazire): Is it useful, or does venv work as standalone ?
# RUN pip3 install virtualenv

RUN chown -R giskard:0 /var/run/postgresql /var/lib/nginx

ENV JAVA_HOME /user/java/jdk17
ENV PATH $JAVA_HOME/bin:$PATH

COPY --from=build-backend /giskard-jre $JAVA_HOME
COPY --from=build-backend /app/backend/build/libs/backend*.jar $GSK_DIST_PATH/backend/giskard.jar

COPY --from=build-frontend /app/frontend/dist $GSK_DIST_PATH/frontend/dist

COPY --from=build-python /app/python-client/dist $GSK_DIST_PATH/python-client
COPY --from=build-python /app/python-client/.venv-prod $VENV_PATH

COPY supervisord.conf ./
COPY packaging/nginx.conf.template $GSK_DIST_PATH/frontend/
COPY scripts/file-guard.sh $GSK_DIST_PATH/file-guard.sh
COPY scripts/start-*.sh $GSK_DIST_PATH/

RUN touch $GSK_DIST_PATH/frontend/nginx.conf && chown giskard $GSK_DIST_PATH/frontend/nginx.conf
USER giskard
WORKDIR $GSK_HOME

ENTRYPOINT ["supervisord", "-c", "/opt/giskard/supervisord.conf"]
EXPOSE 7860