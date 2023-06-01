from typing import Any, Union

from giskard.ml_worker.core.test_result import TestResult
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest


def run_test(test_func: Any, kwargs) -> Union[bool, TestResult]:
    result = test_func(**kwargs)
    if isinstance(result, GiskardTest):
        return result.execute()
    else:
        return result
