import pytest

from giskard.core.suite import single_binary_result
from giskard.ml_worker.testing.test_result import TestResult


@pytest.mark.parametrize(
    "results, single_result",
    [
        ([True, True, True], True),
        ([False, False, True], False),
        ([True, True, False], False),
        ([True, False, True], False),
        ([False, False, False], False),
    ],
)
def test_single_binary_result(results, single_result):
    assert single_binary_result([TestResult(passed=result) for result in results]) is single_result
