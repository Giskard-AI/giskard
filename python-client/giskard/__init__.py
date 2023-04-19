# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

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
from giskard.ml_worker.testing.tests.drift import test_drift_psi, test_drift_chi_square, test_drift_ks, \
    test_drift_earth_movers_distance, test_drift_prediction_psi, test_drift_prediction_chi_square, \
    test_drift_prediction_ks, test_drift_prediction_earth_movers_distance
from giskard.ml_worker.testing.tests.metamorphic import test_metamorphic_invariance, test_metamorphic_increasing, \
    test_metamorphic_decreasing, test_metamorphic_decreasing_t_test, test_metamorphic_increasing_t_test, \
    test_metamorphic_invariance_t_test, test_metamorphic_decreasing_wilcoxon, test_metamorphic_invariance_wilcoxon, \
    test_metamorphic_increasing_wilcoxon
from giskard.ml_worker.testing.tests.performance import AucTest, test_mae, test_rmse, test_recall, test_auc, \
    test_accuracy, test_precision, test_f1, test_r2, test_diff_recall, test_diff_accuracy, test_diff_precision, \
    test_diff_rmse, test_diff_f1, test_diff_reference_actual_rmse, test_diff_reference_actual_accuracy, \
    test_diff_reference_actual_f1
from giskard.ml_worker.testing.tests.statistic import test_right_label, test_output_in_range, test_disparate_impact
from giskard.ml_worker.utils.logging import configure_logging
from giskard.models import wrap_model, model_from_catboost, model_from_huggingface, model_from_tensorflow, \
    model_from_pytorch, model_from_sklearn
from giskard.models.base import WrapperModel, CustomModel, MLFlowBasedModel, BaseModel

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
    'test_disparate_impact',
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
    'test_diff_reference_actual_f1',
    'test_metamorphic_invariance',
    'test_metamorphic_increasing',
    'test_metamorphic_decreasing',
    'test_metamorphic_decreasing_t_test',
    'test_metamorphic_increasing_t_test',
    'test_metamorphic_invariance_t_test',
    'test_metamorphic_increasing_wilcoxon',
    'test_metamorphic_decreasing_wilcoxon',
    'test_metamorphic_invariance_wilcoxon',
    'slicing_function',
    'transformation_function',
    'SuiteInput',
    'SlicingFunction',
    'TestResult',
    'GiskardTest'
]
try:
    from giskard.models.catboost import CatboostModel

    __all__.append('CatboostModel')
except ImportError:
    pass

try:
    from giskard.models.huggingface import HuggingFaceModel

    __all__.append('HuggingFaceModel')
except ImportError:
    pass

try:
    from giskard.models.pytorch import PyTorchModel

    __all__.append('PyTorchModel')
except ImportError:
    pass

try:
    from giskard.models.sklearn import SKLearnModel

    __all__.append('SKLearnModel')
except ImportError:
    pass

try:
    from giskard.models.tensorflow import TensorFlowModel

    __all__.append('TensorFlowModel')
except ImportError:
    pass
