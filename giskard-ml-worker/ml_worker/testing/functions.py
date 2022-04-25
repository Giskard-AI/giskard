from typing import List

from generated.ml_worker_pb2 import SingleTestResult, NamedSingleTestResult
from ml_worker.testing.heuristic_tests import HeuristicTests
from ml_worker.testing.metamorphic_tests import MetamorphicTests
from ml_worker.testing.performance_tests import PerformanceTests

EMPTY_SINGLE_TEST_RESULT = SingleTestResult()


class GiskardTestFunctions:
    tests_results: List[NamedSingleTestResult]
    metamorphic: MetamorphicTests
    heuristic: HeuristicTests
    performance: PerformanceTests

    def __init__(self) -> None:
        self.tests_results = []
        self.metamorphic = MetamorphicTests(self.tests_results)
        self.heuristic = HeuristicTests(self.tests_results)
        self.performance = PerformanceTests(self.tests_results)
