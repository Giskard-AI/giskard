import numpy as np
import pytest

from giskard import Model, Suite
from giskard.core.suite import single_binary_result
from giskard.ml_worker.testing.test_result import TestResult
from giskard.testing import test_accuracy


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
    with pytest.raises(ValueError):
        suite.run()

    # But we can pass dataset at runtime
    suite.run(dataset=german_credit_data)

    # Or we can provide it in the suite defaults
    suite.default_params["dataset"] = german_credit_data
    suite.run()


def test_runtime_parameters_override_default_parameters(german_credit_data, german_credit_model):
    my_test = test_accuracy(threshold=0.7)

    def constant_pred(df):
        return np.stack((np.ones(len(df)), np.zeros(len(df)))).T

    bad_model = Model(
        constant_pred, model_type="classification", classification_labels=german_credit_model.meta.classification_labels
    )

    # The test will not pass
    suite = Suite(default_params=dict(model=bad_model, dataset=german_credit_data))
    suite.add_test(my_test)
    assert not suite.run().passed

    # With the right model, the test will pass
    assert suite.run(model=german_credit_model).passed
