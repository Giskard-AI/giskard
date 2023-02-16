from enum import Enum

from giskard.core.model_validation import validate_model
from giskard.core.model import Model
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.core.suite import Suite, SuiteInput

from giskard.ml_worker.testing.tests.performance import test_auc, test_f1, test_diff_f1

from IPython.display import display
import ipywidgets as widgets

class ScanType(str, Enum):
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    DRIFT = "drift"
    #etc.

def is_notebook():
    try:
        get_ipython()
        return True
    except:
        return False

def test_performance( my_model: Model, my_dataset: Dataset, _is_notebook: bool):
    tot_res , list_res =  Suite() \
        .add_test(test_auc, threshold=0.8) \
        .add_test(test_f1, threshold=0.8) \
        .run(actual_slice=my_dataset, model=my_model)
    if not tot_res:
        if _is_notebook:
            w = widgets.ToggleButtons(
                options=['Fail', 'Pass'],
                description='Performance:',
                disabled=False,
                button_style='', # 'success', 'info', 'warning', 'danger' or ''
                style={"description_width": "auto"},
                tooltips=['Description of slow', 'Description of regular', 'Description of fast'],
                value='Fail',
                #     icons=['check'] * 3
            )
            display(w)
        else:
            print("Your model failed some performance tests!")



def _scan(model: Model,
          validate_ds: Dataset,
          scan_type: str,
          _is_notebook: bool):

    if scan_type == ScanType.VALIDATION:
        validate_model(model, validate_ds)
        print("Your model and dataset passed the validation, and can be safely uploaded to Giskard!")
    if scan_type == ScanType.PERFORMANCE:
        test_performance(model, validate_ds, _is_notebook)

def scan(model: Model,
         validate_ds: Dataset,
         scan_types: any):

    _is_notebook = is_notebook()

    if isinstance(scan_types, list):
        for scan_type in scan_types:
            _scan(model, validate_ds, scan_type, _is_notebook)
    else:
        _scan(model, validate_ds, scan_types, _is_notebook)
