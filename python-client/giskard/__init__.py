# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

import sys

from giskard.client.giskard_client import GiskardClient
from giskard.client.project import Project
from giskard.datasets import dataset
from giskard.datasets.base import Dataset
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.utils.logging import configure_logging
from giskard.models import model, model_from_catboost, model_from_sklearn, \
    model_from_pytorch, model_from_tensorflow, model_from_huggingface
from giskard.models.base import Model
from giskard.models.base import WrapperModel
from giskard.models.base import MLFlowBasedModel
from giskard.models.sklearn import SKLearnModel
from giskard.models.catboost import CatboostModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.tensorflow import TensorFlowModel
from giskard.models.huggingface import HuggingFaceModel

configure_logging()
if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


__version__: str = get_version()

__all__ = [
    'SingleTestResult',
    'Project',
    'dataset',
    'Dataset',
    'GiskardClient',
    'AbstractTestCollection',
    'test',
    'model',
    'model_from_catboost',
    'model_from_sklearn',
    'model_from_pytorch',
    'model_from_tensorflow',
    'model_from_huggingface',
    'Model',
    'WrapperModel',
    'MLFlowBasedModel',
    'SKLearnModel',
    'CatboostModel',
    'PyTorchModel',
    'TensorFlowModel',
    'HuggingFaceModel'
]
