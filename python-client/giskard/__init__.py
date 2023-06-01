# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

import sys

from giskard.client.giskard_client import GiskardClient
from giskard.client.project import Project
from giskard.datasets import dataset
from giskard.datasets.base import Dataset
from giskard.ml_worker.core.suite import Suite
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.testing.tests.drift import test_drift_psi, test_drift_chi_square, test_drift_ks, \
    test_drift_earth_movers_distance, test_drift_prediction_psi, test_drift_prediction_chi_square, \
    test_drift_prediction_ks, test_drift_prediction_earth_movers_distance
from giskard.ml_worker.testing.tests.heuristic import test_right_label, test_output_in_range
from giskard.ml_worker.testing.tests.performance import AucTest, test_mae, test_rmse, test_recall, test_auc, \
    test_accuracy, test_precision, test_f1, test_r2, test_diff_recall, test_diff_accuracy, test_diff_precision, \
    test_diff_rmse, test_diff_f1, test_diff_reference_actual_rmse, test_diff_reference_actual_accuracy, \
    test_diff_reference_actual_f1
from giskard.ml_worker.utils.logging import configure_logging
from giskard.models import model, model_from_catboost, model_from_huggingface, model_from_tensorflow, \
    model_from_pytorch, model_from_sklearn
from giskard.models.base import WrapperModel, CustomModel, MLFlowBasedModel, BaseModel
from giskard.models.catboost import CatboostModel
from giskard.models.huggingface import HuggingFaceModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.sklearn import SKLearnModel
from giskard.models.tensorflow import TensorFlowModel

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
    'BaseModel',
    'WrapperModel',
    'MLFlowBasedModel',
    'CustomModel',
    'SKLearnModel',
    'CatboostModel',
    'PyTorchModel',
    'TensorFlowModel',
    'HuggingFaceModel',
    'Suite',
    'test_drift_psi',
    'test_drift_chi_square',
    'test_drift_ks',
    'test_drift_earth_movers_distance',
    'test_drift_prediction_psi',
    'test_drift_prediction_chi_square',
    'test_drift_prediction_ks',
    'test_drift_prediction_earth_movers_distance',
    'test_right_label',
    'test_output_in_range',
    'AucTest',
    'test_mae',
    'test_rmse',
    'test_recall',
    'test_auc',
    'test_accuracy',
    'test_precision',
    'test_f1',
    'test_r2',
    'test_diff_recall',
    'test_diff_accuracy',
    'test_diff_precision',
    'test_diff_rmse',
    'test_diff_f1',
    'test_diff_reference_actual_rmse',
    'test_diff_reference_actual_accuracy',
    'test_diff_reference_actual_f1'

]
