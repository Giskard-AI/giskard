from enum import Enum

from giskard.core.model_validation import validate_model
from giskard.core.model import Model
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.core.suite import Suite, SuiteInput

from giskard.ml_worker.testing.tests.performance import test_auc, test_f1, test_diff_f1


class ScanType(str, Enum):
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    DRIFT = "drift"
    #etc.

if hasattr(__builtins__, '__IPYTHON__'):
    _in_ipython_session = True
else:
    _in_ipython_session = False

def test_performance( my_model: Model, my_dataset: Dataset):
    output =  Suite() \
        .add_test(test_auc, threshold=0.8) \
        .add_test(test_f1, threshold=0.8) \
        .run(actual_slice=my_dataset, model=my_model)[0]
    print(output)

def _scan(model: Model,
          validate_ds: Dataset,
          scan_type: str):

    if scan_type == ScanType.VALIDATION:
        validate_model(model, validate_ds)
    if scan_type == ScanType.PERFORMANCE:
        test_performance(model, validate_ds)

def scan(model: Model,
         validate_ds: Dataset,
         scan_types: any):

    if isinstance(scan_types, list):
        for scan_type in scan_types:
            _scan(model, validate_ds, scan_type)
    else:
        _scan(model, validate_ds, scan_types)
