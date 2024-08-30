# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""

# The following code block is made to remove pydantic 2.0 warnings, especially for MLFlow
# https://docs.python.org/3/library/warnings.html#temporarily-suppressing-warnings
from importlib import metadata as importlib_metadata

from . import demo
from .client.giskard_client import GiskardClient
from .client.project import Project
from .core.suite import Suite, SuiteInput
from .core.test_result import TestResult
from .datasets.base import Dataset
from .ml_worker.utils.network import check_latest_giskard_version
from .models.automodel import Model
from .models.model_explanation import explain_with_shap
from .registry.decorators import test
from .registry.giskard_test import GiskardTest
from .registry.slicing_function import SlicingFunction, slicing_function
from .registry.transformation_function import TransformationFunction, transformation_function
from .scanner import scan
from .utils.analytics_collector import analytics
from .utils.logging_utils import configure_logging

configure_logging()


def get_version() -> str:
    try:
        res = importlib_metadata.version(__name__)
        if res is None:
            # importlib_metadata can return None https://github.com/python/importlib_metadata/issues/371
            # fallback to pkg_resources even if it's deprecated
            import pkg_resources

            return pkg_resources.get_distribution(__name__).version
        return res
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
