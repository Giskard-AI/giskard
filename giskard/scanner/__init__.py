from typing import Optional

from ..datasets.base import Dataset
from ..models.base import BaseModel
from .logger import logger
from .scanner import Scanner


def _register_default_detectors():
    import importlib
    from pathlib import Path

    root = Path(__file__).parent
    modules = ["." + ".".join(p.relative_to(root).with_suffix("").parts) for p in root.glob("**/*_detector.py")]

    for detector_module in modules:
        importlib.import_module(detector_module, package=__package__)


_register_default_detectors()


def scan(
    model: BaseModel,
    dataset: Optional[Dataset] = None,
    params=None,
    only=None,
    verbose=True,
    raise_exceptions=False,
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
    """
    scanner = Scanner(params, only=only)
    return scanner.analyze(model, dataset, verbose=verbose, raise_exceptions=raise_exceptions)


__all__ = ["scan", "Scanner", "logger"]
