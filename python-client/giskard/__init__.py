# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

import sys

from giskard.client.giskard_client import GiskardClient
from giskard.client.project import Project
from giskard.core.suite import Suite, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
from giskard.ml_worker.testing.registry.slicing_function import slicing_function
from giskard.ml_worker.testing.registry.transformation_function import transformation_function
from giskard.ml_worker.testing.test_result import TestResult
from giskard.ml_worker.utils.logging import configure_logging
from giskard.models.automodel import Model
from giskard.models.model_explanation import explain_with_shap
from giskard import push
from . import demo
from .ml_worker.utils.network import check_latest_giskard_version
from .scanner import scan
from .utils.analytics_collector import analytics

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

check_latest_giskard_version()
analytics.track("Initialized giskard library")

__all__ = [
    "Project",
    "Dataset",
    "GiskardClient",
    "test",
    "push",
    "Model",
    "Suite",
    "slicing_function",
    "transformation_function",
    "SuiteInput",
    "SlicingFunction",
    "TransformationFunction",
    "scan",
    "explain_with_shap",
    "TestResult",
    "GiskardTest",
    "demo",
]
