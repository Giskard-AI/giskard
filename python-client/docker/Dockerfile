# `python-base` sets up all our shared environment variables
FROM python:3.7.13-buster as python-base

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
    POETRY_VERSION=1.2.2 \
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

ENV PATH="$VENV_PATH/bin:$POETRY_HOME/bin:$PATH"


# `builder-base` stage is used to build deps + create our virtual environment
FROM python-base as builder-base

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        git \
        curl \
        build-essential vim

RUN pip install --upgrade pip && \
    pip install -U pip setuptools

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python3 -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY ./python-client/pyproject.toml ./python-client/poetry.lock ./

# install deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --only main ; fi"



# the libraries below are required for demo projects

# Catboost can't be installed on ARM machines, so skip it if it fails
RUN pip install catboost==1.0.6; exit 0

RUN pip install  \
    torch==1.12.0 \
    transformers==4.20.1 \
    nlpaug==1.1.11
# ------------------------------------------------------------------------
# Add your python dependencies here, for example
# RUN pip install catboost transformers "tensorflow^2.9.1"
# ------------------------------------------------------------------------


FROM builder-base as proto-builder

WORKDIR $PYSETUP_PATH
# install dev dependencies needed to protobuf code generation
RUN poetry install --only main,dev

COPY ./python-client/giskard ./giskard
COPY ./common/proto ./proto
COPY ./python-client/scripts ./scripts

# generate grpc stubs
RUN mkdir -p giskard/ml_worker/generated && \
    python -m grpc_tools.protoc \
      -Iproto \
      --python_out=giskard/ml_worker/generated \
      --grpc_python_out=giskard/ml_worker/generated \
      --mypy_out=giskard/ml_worker/generated \
      --mypy_grpc_out=giskard/ml_worker/generated \
      proto/ml-worker.proto && \
    python scripts/fix_grpc_generated_imports.py giskard/ml_worker/generated giskard.ml_worker.generated



# `production` image used for runtime
FROM python-base as production
COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --from=proto-builder $PYSETUP_PATH/giskard $PYSETUP_PATH/giskard

WORKDIR $PYSETUP_PATH

ENV GSK_HOST=0.0.0.0
ENV PYTHONPATH=.

CMD ["python", "giskard/cli.py", "worker", "start", "-s"]
EXPOSE 50051
