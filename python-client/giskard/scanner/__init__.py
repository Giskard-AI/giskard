from ..models.base import BaseModel
from ..datasets.base import Dataset
from .scanner import Scanner
from .logger import logger

_default_detectors = [
    ".performance.performance_bias_detector",
    ".robustness.text_perturbation_detector",
    ".data_leakage.data_leakage_detector",
    ".stochasticity.stochasticity_detector",
    ".calibration.overconfidence_detector",
    ".calibration.underconfidence_detector",
]


def _register_default_detectors():
    import importlib

    for _default_detector in _default_detectors:
        importlib.import_module(_default_detector, package=__package__)


_register_default_detectors()


def scan(model: BaseModel, dataset: Dataset, params=None, only=None, verbose=True):
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
    scanner = Scanner(params, only=only)
    return scanner.analyze(model, dataset, verbose=verbose)


__all__ = ["scan", "Scanner", "logger"]
