from ..models.base import _BaseModel
from .. import Dataset
from .scanner import Scanner


_default_detectors = [
    ".performance.model_bias_detector",
]


def _register_default_detectors():
    import importlib

    for _default_detector in _default_detectors:
        importlib.import_module(_default_detector, package=__package__)


_register_default_detectors()


def scan(model: _BaseModel, dataset: Dataset, params=None, only=None):
    """
    Scan a model with a dataset.

    Args:
        model (_BaseModel):
            A Giskard model object.
        dataset (Dataset):
            A Giskard dataset object.
        params (dict):
            Scanner configuration.
    """
    scanner = Scanner(params, only=only)
    return scanner.analyze(model, dataset)


__all__ = ["scan", "Scanner"]
