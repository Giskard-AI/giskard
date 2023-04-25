# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

import datetime

start = datetime.datetime.now()

import sys

from giskard.client.giskard_client import GiskardClient
from giskard.client.project import Project
from giskard.datasets import wrap_dataset
from giskard.datasets.base import Dataset
from giskard.ml_worker.core.suite import Suite, SuiteInput
from giskard.ml_worker.core.test_result import TestResult
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.slicing_function import slicing_function
from giskard.ml_worker.testing.registry.transformation_function import transformation_function
from giskard.ml_worker.utils.logging import configure_logging
from giskard.models import wrap_model, model_from_catboost, model_from_huggingface, model_from_tensorflow, \
    model_from_pytorch, model_from_sklearn
from giskard.models.base import WrapperModel, CustomModel, MLFlowBasedModel, BaseModel
from .scanner import scan

configure_logging()


def get_version() -> str:
    if sys.version_info >= (3, 8):
        from importlib import metadata as importlib_metadata
    else:
        import importlib_metadata
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


__version__: str = get_version()

__all__ = [
    'SingleTestResult',
    'Project',
    'wrap_dataset',
    'Dataset',
    'GiskardClient',
    'test',
    'wrap_model',
    'model_from_catboost',
    'model_from_sklearn',
    'model_from_pytorch',
    'model_from_tensorflow',
    'model_from_huggingface',
    'BaseModel',
    'WrapperModel',
    'MLFlowBasedModel',
    'CustomModel',
    'Suite',
    'slicing_function',
    'transformation_function',
    'SuiteInput',
    'SlicingFunction',
    'scan',
    'TestResult',
    'GiskardTest',
]
