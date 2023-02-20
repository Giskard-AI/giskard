FROM ubuntu:latest as build

# >>> BACKEND

RUN apt-get update
RUN apt -y install openjdk-17-jdk

ENV _JAVA_OPTIONS="-Xmx4048m -Xms512m" \
    SPRING_PROFILES_ACTIVE=prod \
    MANAGEMENT_METRICS_EXPORT_PROMETHEUS_ENABLED=true \
    SPRING_DATASOURCE_USERNAME=postgres

WORKDIR /app

COPY supervisord.conf /etc/
COPY gradle gradle
COPY gradlew .
COPY gradle.properties .
COPY settings.gradle.kts .
COPY build.gradle.kts .
COPY .git .git
COPY common common

COPY backend backend

WORKDIR /app/backend

ARG RUN_TESTS=false

RUN bash -c " \
    echo RUN_TESTS=$RUN_TESTS && \
    if [ "$RUN_TESTS" = true ] ;  \
      then  ../gradlew -Pprod clean test bootJar --info --stacktrace;  \
      else  ../gradlew -Pprod clean bootJar --info --stacktrace ;  \
    fi"

# <<< BACKEND

# >>> FRONTEND

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN apt-get update -y && apt-get install -y libxml2-dev libgcrypt-dev npm
RUN npm install

COPY frontend/ ./
ARG FRONTEND_ENV=production
ENV VUE_APP_ENV=${FRONTEND_ENV}
RUN npm run build

# <<< FRONTEND

# >>> ML-WORKER

FROM python:3.7.13 as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$VENV_PATH/bin:$POETRY_HOME/bin:$PATH"

FROM python-base as builder-base

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        git \
        curl \
        build-essential vim

RUN pip install --upgrade pip && \
    pip install -U pip setuptools

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH

COPY ./python-client/pyproject.toml ./python-client/poetry.lock ./

ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --only main ; fi"

RUN pip install  \
    torch==1.12.0 \
    transformers==4.20.1 \
    nlpaug==1.1.11

FROM builder-base as proto-builder

WORKDIR $PYSETUP_PATH

RUN poetry install --only main,dev
COPY ./common/proto ./proto
COPY ./python-client/giskard ./giskard
COPY ./python-client/scripts ./scripts

RUN mkdir -p giskard/ml_worker/generated && \
    python -m grpc_tools.protoc \
      -Iproto \
      --python_out=giskard/ml_worker/generated \
      --grpc_python_out=giskard/ml_worker/generated \
      --mypy_out=giskard/ml_worker/generated \
      --mypy_grpc_out=giskard/ml_worker/generated \
      proto/ml-worker.proto && \
    python scripts/fix_grpc_generated_imports.py giskard/ml_worker/generated giskard.ml_worker.generated

# <<< ML-WORKER

# >>> FINAL CONFIGURATION

FROM python-base as production
ENV SPRING_PROFILES_ACTIVE=prod


ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
    postgresql \
    nginx \
    openjdk-17-jre \
    supervisor

ENV PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    PGDATA=/var/lib/postgresql/data/pgdata \
    SPRING_DATASOURCE_USERNAME=postgres \
    SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/app \
    SPRING_LIQUIBASE_URL=jdbc:postgresql://localhost:5432/app

ENV PATH="$VENV_PATH/bin:$POETRY_HOME/bin:$PATH"

WORKDIR /app

COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --from=proto-builder $PYSETUP_PATH/giskard $PYSETUP_PATH/giskard
COPY --from=build /app/backend/build/libs/backend*.jar /app/backend/lib/giskard.jar
COPY --from=build /etc/supervisord.conf /app/
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY supervisord.conf /app/supervisord.conf

COPY frontend/packaging/nginx_single_dockerfile.conf /etc/nginx/sites-enabled/default.conf

RUN rm /etc/nginx/sites-enabled/default

ENV GSK_HOST=0.0.0.0
ENV PYTHONPATH=$PYSETUP_PATH

RUN mkdir /var/lib/postgresql/data /root/giskard-home

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

# <<< FINAL CONFIGURATION
