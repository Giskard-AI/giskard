import pytest

from giskard.core.test_result import TestMessage, TestMessageLevel, TestResult
from giskard.registry.decorators import test as testdec


@testdec(name="Boolean")
def tst_boolean(passed: bool):
    return passed


@testdec(name="No Message")
def tst_without_message(passed: bool):
    return TestResult(passed=passed, metric=0)


@testdec(name="With Message")
def tst_with_message(passed: bool):
    return TestResult(
        passed=passed,
        metric=0,
        messages=[
            TestMessage(TestMessageLevel.INFO, "hello"),
            TestMessage(TestMessageLevel.INFO, "world"),
        ],
    )


def test_failed_test_boolean():
    with pytest.raises(AssertionError) as e:
        tst_boolean(passed=False).assert_()

    assert str(e.value.args[0].split("\n")[0]) == "assert False"


def test_failed_test_no_message():
    with pytest.raises(AssertionError) as e:
        tst_without_message(passed=False).assert_()

    assert str(e.value.args[0].split("\n")[0]) == "Test failed Metric: 0"


def test_failed_test_with_message():
    with pytest.raises(AssertionError) as e:
        tst_with_message(passed=False).assert_()

    assert str(e.value.args[0].split("\n")[0]) == "hello world"


def test_pass_test_boolean():
    tst_boolean(passed=True).assert_()


def test_pass_test_no_message():
    tst_without_message(passed=True).assert_()


def test_pass_test_with_message():
    tst_with_message(passed=True).assert_()
