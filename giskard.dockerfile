FROM ubuntu:latest as build

# >>> BACKEND

RUN apt-get update
RUN apt -y install openjdk-17-jdk

ENV _JAVA_OPTIONS="-Xmx4048m -Xms512m" \
    SPRING_PROFILES_ACTIVE=prod \ 
    MANAGEMENT_METRICS_EXPORT_PROMETHEUS_ENABLED=true \
    SPRING_DATASOURCE_USERNAME=postgres

WORKDIR /app/giskard-server

COPY supervisord.conf /etc/
COPY giskard-server/gradle gradle
COPY giskard-server/ml-worker-proto ml-worker-proto
COPY giskard-server/src src
COPY giskard-server/build.gradle .
COPY giskard-server/sonar-project.properties .

WORKDIR /app

COPY gradle gradle
COPY gradlew .
COPY gradle.properties .
COPY settings.gradle .
COPY build.gradle .
COPY .git .git

ARG RUN_TESTS=false

RUN bash -c "if [ "$RUN_TESTS" = true ] ; then  ./gradlew -Pprod clean test bootJar ; else ./gradlew -Pprod clean bootJar ; fi"

# <<< BACKEND

# >>> FRONTEND

WORKDIR /app/frontend

COPY ./giskard-frontend/package*.json .

RUN apt-get update -y && apt-get install -y libxml2-dev libgcrypt-dev npm 
RUN npm install

COPY ./giskard-frontend/ ./
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

RUN git clone https://github.com/Giskard-AI/giskard-client.git
RUN cd giskard-client && git submodule update --init --recursive
RUN mv giskard-client/* . && rm -rf giskard-client

ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --only main ; fi"

RUN pip install  \
    torch==1.12.0 \
    transformers==4.20.1 \
    nlpaug==1.1.11

FROM builder-base as proto-builder

WORKDIR $PYSETUP_PATH
RUN poetry install --only main,dev

RUN make generate-proto

# <<< ML-WORKER

# >>> FINAL CONFIGURATION

FROM python-base as production

ENV SPRING_PROFILES_ACTIVE=prod


ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y postgresql
RUN apt-get install -y lsof
RUN apt-get -y install nginx
RUN apt-get -y install openjdk-17-jre
RUN apt-get -y install supervisor

ENV PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \ 
    PGDATA=/var/lib/postgresql/data/pgdata \
    SPRING_DATASOURCE_USERNAME=postgres \
    SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/app \
    SPRING_LIQUIBASE_URL=jdbc:postgresql://localhost:5432/app

ENV PATH="$VENV_PATH/bin:$POETRY_HOME/bin:$PATH"

COPY --from=build /app/giskard-server/build/libs/giskard*.jar giskard/lib/giskard.jar

COPY --from=proto-builder $PYSETUP_PATH/giskard $PYSETUP_PATH/giskard
COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --from=build /etc/supervisord.conf /etc/

COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY giskard-frontend/packaging/nginx_single_dockerfile.conf /etc/nginx/sites-enabled/default.conf
RUN rm /etc/nginx/sites-enabled/default 

ENV GSK_HOST=0.0.0.0
ENV PYTHONPATH=$PYSETUP_PATH


VOLUME /root/giskard-home

ENTRYPOINT ["supervisord", "-c", "/etc/supervisord.conf"]

# <<< FINAL CONFIGURATION