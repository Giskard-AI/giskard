FROM python:3.10 as build

RUN apt-get update
RUN apt-get -y install openjdk-17-jdk-headless

ARG RUN_TESTS=false
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
COPY python-client python-client
COPY frontend frontend
COPY backend backend
COPY common common
COPY gradle gradle
# Copying .git to make gradle-git-properties gradle plugin work
COPY .git .git

COPY build.gradle.kts gradle.properties gradlew settings.gradle.kts ./

RUN ./gradlew clean install -Pprod --parallel --info --stacktrace
RUN ./gradlew :backend:package -Pprod --parallel --info --stacktrace
RUN ./gradlew :frontend:package -Pprod --parallel --info --stacktrace
RUN ./gradlew :python-client:package -Pprod --parallel --info --stacktrace


# Create an environment and install giskard wheel. Some dependencies may require gcc which is only installed in build
# stage, but not in the production one
RUN python3 -m virtualenv python-client/.venv-prod
RUN WHEEL=$(ls python-client/dist/giskard*.whl) && python-client/.venv-prod/bin/pip install $WHEEL\[server\]



FROM python:3.10-slim
ENV SPRING_PROFILES_ACTIVE=prod
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
    postgresql nginx openjdk-17-jre-headless supervisor git gettext-base

ENV SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/postgres \
    SPRING_LIQUIBASE_URL=jdbc:postgresql://localhost:5432/postgres \
    GSK_HOST=0.0.0.0 \
    GSK_USER_HOME=/home/giskard \
    GSK_HOME=/home/giskard/datadir \
    GSK_DIST_PATH=/opt/giskard

ENV VENV_PATH=$GSK_DIST_PATH/internal-mlworker-venv

ENV PATH="$VENV_PATH/bin:/usr/lib/postgresql/13/bin:$PATH" \
    PGDATA=$GSK_HOME/database \
    GISKARD_HOME=$GSK_HOME

WORKDIR $GSK_DIST_PATH

COPY --from=build /app/python-client/.venv-prod $VENV_PATH
COPY --from=build /app/backend/build/libs/backend*.jar $GSK_DIST_PATH/backend/giskard.jar
COPY --from=build /app/frontend/dist $GSK_DIST_PATH/frontend/dist

COPY supervisord.conf ./
COPY packaging/nginx.conf.template $GSK_DIST_PATH/frontend/

ARG GISKARD_UID=50000

RUN adduser --gecos "First Last,RoomNumber,WorkPhone,HomePhone" --disabled-password \
       --quiet "giskard" --uid "${GISKARD_UID}" --gid "0" --home "${GSK_USER_HOME}" && \
    mkdir -p "${GSK_HOME}/run" && chown -R "giskard:0" "${GSK_USER_HOME}" "${GSK_DIST_PATH}"

RUN chown -R giskard:0 /var/run/postgresql /var/lib/nginx

USER giskard
WORKDIR $GSK_HOME

ENTRYPOINT ["supervisord", "-c", "/opt/giskard/supervisord.conf"]
