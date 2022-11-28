from typing import List

import inspect
import logging
from abc import ABC

from giskard.ml_worker.generated.ml_worker_pb2 import NamedSingleTestResult, SingleTestResult

logger = logging.getLogger(__name__)


class AbstractTestCollection(ABC):
    tests_results: List[NamedSingleTestResult]
    do_save_results = True

    def __init__(self, test_results: List[NamedSingleTestResult]) -> None:
        self.tests_results = test_results

    @staticmethod
    def _find_caller_test_name():
        stack = inspect.stack()
        for frame in stack:
            if frame.function.startswith("test_"):
                return frame.function
        logger.warning(f"Failed to extract test method name")

    def save_results(self, result: SingleTestResult, test_name=None):
        if not self.do_save_results:
            return result
        if test_name is None:
            test_name = self._find_caller_test_name()

        self.tests_results.append(NamedSingleTestResult(name=test_name, result=result))
        return result
