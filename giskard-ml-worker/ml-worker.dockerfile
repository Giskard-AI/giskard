# `python-base` sets up all our shared environment variables
FROM python:3.7-slim as python-base

    # python
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VERSION=1.1.13 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"


# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


# `builder-base` stage is used to build deps + create our virtual environment
FROM python-base as builder-base
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        git \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY ./giskard-ml-worker/pyproject.toml ./giskard-ml-worker/poetry.lock* ./

# install deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"



FROM builder-base as proto-builder
WORKDIR $PYSETUP_PATH
# install dev dependencies needed to protobuf code generation
RUN poetry install

# copy makefile and proto to generate python sources
WORKDIR /app

RUN mkdir "generated"
COPY ./giskard-common/proto proto

RUN python3.7 -m grpc_tools.protoc \
      -Iproto \
      --python_out=generated \
      --grpc_python_out=generated \
      --mypy_out=generated \
      proto/ml-worker.proto

# `production` image used for runtime
FROM python-base as production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY ./giskard-ml-worker /app

WORKDIR /app
COPY --from=proto-builder /app/generated ./generated

# replace symlinked directory by actual copy
# Docker preserves symlinks when its parent is copied and copies real files when only synlink is copied
RUN rm -rf ./ml_worker/core
COPY ./giskard-ml-worker/ml_worker/core ./ml_worker/core
ENV PYTHONPATH "/app/generated"

CMD ["python", "main.py"]