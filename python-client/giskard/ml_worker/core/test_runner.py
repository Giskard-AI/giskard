from typing import Any

from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest


def run_test(test_func: Any, kwargs) -> SingleTestResult:
    result = test_func(**kwargs)
    if isinstance(result, GiskardTest):
        return result.execute()
    else:
        return result
