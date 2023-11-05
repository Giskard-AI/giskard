"""The scanner module provides a way to automatically detect issues in tabular, NLP, and LLM models. It works by running a
set of automatic detectors depending on the model type. The detectors analyze the model and report any issues they find.
"""
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
    """Automatically detects model vulnerabilities.

    See :class:`Scanner` for more details.

    Parameters
    ----------
    model : BaseModel
        A Giskard model object.
    dataset : Dataset
        A Giskard dataset object.
    params : dict
        Advanced scanner configuration. See :class:`Scanner` for more details.
    only : list
        A tag list to limit the scan to a subset of detectors. For example,
        ``giskard.scan(model, dataset, only=["performance"])`` will only run detectors for performance issues.
    verbose : bool
        Whether to print detailed info messages. Enabled by default.
    raise_exceptions : bool
        Whether to raise an exception if detection errors are encountered. By default, errors are logged and
        handled gracefully, without interrupting the scan.

    Returns
    -------
    ScanReport
        A scan report object containing the results of the scan.
    """
    scanner = Scanner(params, only=only)
    return scanner.analyze(model, dataset, verbose=verbose, raise_exceptions=raise_exceptions)


__all__ = ["scan", "Scanner", "logger"]
