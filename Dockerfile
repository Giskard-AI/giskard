FROM python:3.10 as build

RUN apt-get update
RUN apt-get -y install openjdk-17-jdk-headless

ARG RUN_TESTS=false
ARG FRONTEND_ENV=production

ENV _JAVA_OPTIONS="-Xmx4048m -Xms512m" \
    SPRING_PROFILES_ACTIVE=prod \
    MANAGEMENT_METRICS_EXPORT_PROMETHEUS_ENABLED=false \
    SPRING_DATASOURCE_USERNAME=postgres \
    VUE_APP_ENV=${FRONTEND_ENV} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app
# unnecessary files are filtered out by .dockerignore
COPY . .

RUN ./gradlew clean package -Pprod --parallel --info --stacktrace


# Create an environment and install giskard wheel. Some dependencies may require gcc which is only installed in build
# stage, but not in the production one
RUN python3 -m virtualenv python-client/.venv-prod
RUN python-client/.venv-prod/bin/pip install python-client/dist/giskard*.whl



FROM python:3.10-slim
ENV SPRING_PROFILES_ACTIVE=prod
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
    postgresql \
    nginx \
    openjdk-17-jre-headless \
    supervisor \
    git

ENV PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    PGDATA=/var/lib/postgresql/data/pgdata \
    SPRING_DATASOURCE_USERNAME=postgres \
    SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/app \
    SPRING_LIQUIBASE_URL=jdbc:postgresql://localhost:5432/app \
    GSK_HOST=0.0.0.0

ENV PATH="$VENV_PATH/bin:$PATH" \
    PYTHONPATH=$PYSETUP_PATH


WORKDIR /app

COPY --from=build /app/python-client/.venv-prod $VENV_PATH
COPY --from=build /app/backend/build/libs/backend*.jar /app/backend/lib/giskard.jar
COPY --from=build /app/frontend/dist /usr/share/nginx/html

COPY supervisord.conf /app/supervisord.conf
COPY frontend/packaging/nginx_single_dockerfile.conf /etc/nginx/sites-enabled/default.conf

RUN rm /etc/nginx/sites-enabled/default; \
    mkdir /var/lib/postgresql/data /root/giskard-home;

RUN useradd -u 1000 postgres; exit 0
RUN usermod -u 1000 postgres; exit 0

RUN chown -R 1000:1000 /var/run/postgresql && \
    chown -R 1000:1000 /var/log/nginx && \
    chown -R 1000:1000 /var/lib/nginx && \
    chown -R 1000:1000 /etc/nginx && \
    chown -R 1000:1000 /root/giskard-home && \
    chown -R 1000:1000 /var/lib/postgresql/data && \
    chown -R 1000:1000 /run && \
    chown -R 1000:1000 $PYSETUP_PATH && \
    chown -R 1000:1000 /app

ENTRYPOINT ["supervisord", "-c", "/app/supervisord.conf"]
