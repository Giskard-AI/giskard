from typing import Optional

from giskard.core.model_validation import ValidationFlags

from ..datasets.base import Dataset
from ..models.base import BaseModel
from .logger import logger
from .scanner import Scanner

_default_detectors = [
    ".performance.performance_bias_detector",
    ".robustness.text_perturbation_detector",
    ".robustness.ethical_bias_detector",
    ".data_leakage.data_leakage_detector",
    ".stochasticity.stochasticity_detector",
    ".calibration.overconfidence_detector",
    ".calibration.underconfidence_detector",
    ".correlation.spurious_correlation_detector",
    ".llm.toxicity_detector",
    ".llm.harmfulness_detector",
    ".llm.gender_stereotype_detector",
    ".llm.minority_stereotype_detector",
]


def _register_default_detectors():
    import importlib

    for _default_detector in _default_detectors:
        importlib.import_module(_default_detector, package=__package__)


_register_default_detectors()


def scan(
    model: BaseModel,
    dataset: Optional[Dataset] = None,
    params=None,
    only=None,
    verbose=True,
    raise_exceptions=False,
    validation_flags: Optional[ValidationFlags] = ValidationFlags(),
):
    """
    Scan a model with a dataset.

    Args:
        model (BaseModel):
            A Giskard model object.
        dataset (Dataset):
            A Giskard dataset object.
        params (dict):
            Scanner configuration.
        verbose (bool):
            Whether to print information messages. Enabled by default.
        raise_exceptions (bool):
            Whether to raise an exception if detection errors are encountered. By default, errors are logged and
            handled gracefully, without interrupting the scan.
        validation_flags (ValidationFlags):
            Collection of flags to activate/deactivate model_validation flags

    """
    scanner = Scanner(params, only=only)
    return scanner.analyze(
        model, dataset, verbose=verbose, raise_exceptions=raise_exceptions, validation_flags=validation_flags
    )


__all__ = ["scan", "Scanner", "logger"]
