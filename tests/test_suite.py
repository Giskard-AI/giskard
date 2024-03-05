import uuid
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from giskard import Dataset, Model, Suite
from giskard.core.suite import SuiteResult, TestPartial, TestSuiteResult, single_binary_result
from giskard.core.test_result import TestResult
from giskard.testing import test_accuracy
from tests.utils import MockedClient


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


def test_default_parameters_are_used_at_runtime(german_credit_data, german_credit_model):
    my_test = test_accuracy(threshold=0.7)

    # This will miss dataset
    suite = Suite(default_params=dict(model=german_credit_model))
    suite.add_test(my_test)
    result = suite.run()
    assert not result.passed
    _, test_result, _ = result.results[0]
    assert test_result.is_error

    # But we can pass dataset at runtime
    result = suite.run(dataset=german_credit_data)
    assert result.passed
    _, test_result, _ = result.results[0]
    assert not test_result.is_error
    assert test_result.passed

    # Or we can provide it in the suite defaults
    suite.default_params["dataset"] = german_credit_data
    result = suite.run()
    assert result.passed
    _, test_result, _ = result.results[0]
    assert not test_result.is_error
    assert test_result.passed


def test_runtime_parameters_override_default_parameters(german_credit_data, german_credit_model):
    my_test = test_accuracy(threshold=0.7)

    def constant_pred(df):
        return np.stack((np.ones(len(df)), np.zeros(len(df)))).T

    bad_model = Model(
        constant_pred, model_type="classification", classification_labels=german_credit_model.classification_labels
    )

    # The test will not pass
    suite = Suite(default_params=dict(model=bad_model, dataset=german_credit_data))
    suite.add_test(my_test)
    assert not suite.run().passed

    # With the right model, the test will pass
    assert suite.run(model=german_credit_model).passed


def test_export_for_unittest_with_default(german_credit_data, german_credit_model):
    my_test = test_accuracy(threshold=0.7)

    suite = Suite(default_params=dict(model=german_credit_model, dataset=german_credit_data))
    suite.add_test(my_test)
    tests_list = suite.to_unittest()
    assert len(tests_list) == 1
    assert bool(tests_list[0].fullname)


def test_export_for_unittest_with_export_args(german_credit_data, german_credit_model):
    my_test = test_accuracy(threshold=0.7)

    suite = Suite()
    suite.add_test(my_test)
    tests_list = suite.to_unittest(model=german_credit_model, dataset=german_credit_data)
    assert len(tests_list) == 1
    assert bool(tests_list[0].fullname)


def test_suite_result_backward_compatibility():
    """This allow backward compatibility by going moving Suiteresult from a tuple to a dataclass"""
    test_name, result, params = SuiteResult("name", TestResult(), {}, TestPartial(test_accuracy, dict(), 1))
    assert test_name == "name"
    assert result == TestResult()
    assert params == {}


def test_suite_result_to_dto():
    dataset = Dataset(pd.DataFrame({"test": [1, 2, 3]}))
    dataset.id = uuid.uuid4()

    suite = Suite()
    suite.id = 2

    result = TestSuiteResult(
        suite,
        {"dataset": dataset, "threshold": 0.5},
        True,
        [
            SuiteResult(
                "name", TestResult(), {"dataset": dataset, "threshold": 0.5}, TestPartial(test_accuracy, dict(), 1)
            )
        ],
        datetime.now(),
        datetime.now(),
    )

    with MockedClient() as (client, mr):
        dto = result._to_dto("label", client, "project_key")

        assert dto.inputs[0].value == str(dataset.id)
        assert dto.inputs[1].value == str(0.5)

        assert dto.results[0].inputs["dataset"] == str(dataset.id)
        assert dto.results[0].inputs["threshold"] == str(0.5)
