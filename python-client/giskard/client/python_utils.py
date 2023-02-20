"""Various utility functions to manage Python environments"""

import os
import sys
import warnings
from platform import python_version


def get_python_requirements() -> str:
    pip_requirements = os.popen(f"{sys.executable} -m pip list --format freeze").read()
    if pip_requirements:
        return pip_requirements
    else:
        raise RuntimeError(
            "Python requirements could not be resolved. "
            + "Please use one of the following Python package managers: "
            + "Poetry, Pipenv or Pip."
        )


def get_python_version() -> str:
    return python_version()


def warning(content: str):
    warnings.warn(content, stacklevel=2)
