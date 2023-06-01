# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

import sys

from giskard.client.giskard_client import GiskardClient
from giskard.client.project import Project
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.utils.logging import configure_logging
import giskard.model as model
from giskard.core.model import Model
from giskard.core.model import WrapperModel
from giskard.core.model import MLFlowBasedModel
from giskard.model.sklearn import SKLearnModel
from giskard.model.catboost import CatboostModel
from giskard.model.pytorch import PyTorchModel
from giskard.model.tensorflow import TensorFlowModel
from giskard.model.huggingface import HuggingFaceModel

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
    'Dataset',
    'GiskardClient',
    'AbstractTestCollection',
    'test',
    'model',
    'Model',
    'WrapperModel',
    'MLFlowBasedModel',
    'SKLearnModel',
    'CatboostModel',
    'PyTorchModel',
    'TensorFlowModel',
    'HuggingFaceModel'
]
