# type: ignore[attr-defined]
"""Inspect your AI models visually, find bugs, give feedback 🕵️‍♀️ 💬"""
from importlib import metadata as importlib_metadata

from . import demo, push
from .client.giskard_client import GiskardClient
from .client.project import Project
from .core.suite import Suite, SuiteInput
from .datasets.base import Dataset
from .llm.config import llm_config
from .ml_worker.testing.registry.decorators import test
from .ml_worker.testing.registry.giskard_test import GiskardTest
from .ml_worker.testing.registry.slicing_function import SlicingFunction, slicing_function
from .ml_worker.testing.registry.transformation_function import TransformationFunction, transformation_function
from .ml_worker.testing.test_result import TestResult
from .ml_worker.utils.logging import configure_logging
from .ml_worker.utils.network import check_latest_giskard_version
from .models.automodel import Model
from .models.model_explanation import explain_with_shap
from .scanner import scan
from .utils.analytics_collector import analytics

configure_logging()


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
    "llm_config",
]
