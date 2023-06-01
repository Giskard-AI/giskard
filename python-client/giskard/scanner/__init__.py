from ..models.base import BaseModel
from ..datasets.base import Dataset
from ..core.model_validation import validate_model
from .scanner import Scanner


_default_detectors = [
    ".performance.model_bias_detector",
]


def _register_default_detectors():
    import importlib

    for _default_detector in _default_detectors:
        importlib.import_module(_default_detector, package=__package__)


_register_default_detectors()


def scan(model: BaseModel, dataset: Dataset, params=None):
    """
    Scan a model with a dataset.

    Args:
        model (BaseModel):
            A Giskard model object.
        dataset (Dataset):
            A Giskard dataset object.
        params (dict):
            Scanner configuration.
    """
    scanner = Scanner(params)
    return scanner.analyze(model, dataset)


__all__ = ["scan", "Scanner"]
