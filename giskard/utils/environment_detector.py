# The code is taken from https://github.com/interpretml/interpret/blob/develop/python/interpret-core/interpret/provider/_environment.py
# Copyright (c) 2023 The InterpretML Contributors
# Distributed under the MIT software license

import os

""" Environment detection related utilities.
A good portion of this code has largely been sourced from open-source licensed code available
between StackOverflow and plotly.

Plotly derived code comes from below:
https://github.com/plotly/plotly.py/blob/944af4a0b28bef2b139307a7808c02c51d804c4d/packages/python/plotly/plotly/io/_renderers.py#L455
"""


def _detect_ipython():
    """Detects if called in an IPython environment.
    Mostly derived from stackoverflow below:
    https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook

    Returns:
        True if in IPython environment.
    """

    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except NameError:  # pragma: no cover
        return False


def _detect_ipython_zmq():
    """Detects if in an IPython environment using ZMQ (i.e. notebook/qtconsole/lab).

    Mostly derived from stackoverflow below:
    https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook/24937408

    Returns:
        True if called in IPython notebook or qtconsole.
    """
    try:
        from IPython import get_ipython

        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:  # pragma: no cover
        return False  # Probably standard Python interpreter


def _detect_colab():
    try:
        import google.colab  # noqa: F401

        return True
    except ImportError:
        return False


def _detect_binder():
    return "BINDER_SERVICE_HOST" in os.environ


def _detect_sagemaker():
    return "SM_NUM_CPUS" in os.environ


def _detect_kaggle():
    return os.path.exists("/kaggle/input")


def _detect_azure_notebook():
    return "AZURE_NOTEBOOKS_HOST" in os.environ


def _detect_azureml():
    # AzureML seems to have multiple ways to render a notebook or lab.
    # If any of the following succeed, consider it within AzureML
    nbvm_file_path = "/mnt/azmnt/.nbvm"
    azml_notebook_vm_check = os.path.exists(nbvm_file_path) and os.path.isfile(nbvm_file_path)
    azml_notebook_check = "AZUREML_NB_PATH" in os.environ
    azml_lab_check = "LOGNAME" in os.environ and os.environ["LOGNAME"] == "azureuser"
    return azml_notebook_vm_check or azml_notebook_check or azml_lab_check


def _detect_vscode():
    return "VSCODE_PID" in os.environ


def _detect_databricks():
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


def _is_docker_development_mode():
    return os.environ.get("INTERPRET_DOCKER_MODE", None) == "dev"


def _detect_azure_synapse():
    return os.environ.get("AZURE_SERVICE", None) == "Microsoft.ProjectArcadia"


def enum(**enums):
    return type("Enum", (), enums)


ENV_DETECTED = enum(
    CLOUD="CLOUD",
    NON_CLOUD="NON_CLOUD",
    BOTH_CLOUD_AND_NON_CLOUD="BOTH_CLOUD_AND_NON_CLOUD",
)


DOCKER_DEV = "docker-dev-mode"
DATABRICKS = "databricks"
VSCODE = "vscode"
AZURE = "azure"
AZUREML = "azureml"
KAGGLE = "kaggle"
SAGEMAKER = "sagemaker"
BINDER = "binder"
COLAB = "colab"
AZURESYNAPSE = "azuresynapse"
IPYTHON = "ipython"
IPYTHON_ZMQ = "ipython-zmq"


def is_cloud_env(detected):
    non_cloud_env = [
        IPYTHON_ZMQ,
        IPYTHON,
        VSCODE,
    ]
    cloud_env = [
        DATABRICKS,
        AZURE,
        AZUREML,
        KAGGLE,
        SAGEMAKER,
        BINDER,
        COLAB,
        AZURESYNAPSE,
    ]
    if len(set(cloud_env).intersection(detected)) != 0 and len(set(non_cloud_env).intersection(detected)) == 0:
        return ENV_DETECTED.CLOUD
    elif len(set(cloud_env).intersection(detected)) != 0 and len(set(non_cloud_env).intersection(detected)) != 0:
        return ENV_DETECTED.BOTH_CLOUD_AND_NON_CLOUD
    else:
        return ENV_DETECTED.NON_CLOUD


class EnvironmentDetector:
    def __init__(self):
        self.checks = {
            DOCKER_DEV: _is_docker_development_mode,
            DATABRICKS: _detect_databricks,
            VSCODE: _detect_vscode,
            AZURE: _detect_azure_notebook,
            AZUREML: _detect_azureml,
            KAGGLE: _detect_kaggle,
            SAGEMAKER: _detect_sagemaker,
            BINDER: _detect_binder,
            COLAB: _detect_colab,
            IPYTHON_ZMQ: _detect_ipython_zmq,
            IPYTHON: _detect_ipython,
            AZURESYNAPSE: _detect_azure_synapse,
        }

    def detect(self):
        envs = []
        for name, check in self.checks.items():
            try:
                check_passed = check()
            except Exception as e:  # noqa
                check_passed = False
            if check_passed:
                envs.append(name)
        return envs
