import inspect
import logging
from abc import ABC
from typing import List

from generated.ml_worker_pb2 import NamedSingleTestResult, SingleTestResult


class AbstractTestCollection(ABC):
    tests_results: List[NamedSingleTestResult]

    def __init__(self, test_results: List[NamedSingleTestResult]) -> None:
        self.tests_results = test_results

    @staticmethod
    def _find_caller_test_name():
        curr_frame = inspect.currentframe()
        try:
            while curr_frame.f_back.f_code.co_name != '<module>':
                curr_frame = curr_frame.f_back
        except Exception as e:
            logging.error(f"Failed to extract test method name", e)
        return curr_frame.f_code.co_name

    def save_results(self, result: SingleTestResult, test_name=None):
        if test_name is None:
            test_name = self._find_caller_test_name()

        self.tests_results.append(NamedSingleTestResult(name=test_name, result=result))
        return result
