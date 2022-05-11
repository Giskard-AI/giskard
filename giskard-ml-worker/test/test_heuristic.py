import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def _test_heuristic(german_credit_test_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        classification_label='Default',
        threshold=threshold)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 233
    assert results.unexpected_percent == 23.3
    return results.passed


def test_heuristic_opposite(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        'Not default')

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000 - 233
    assert pytest.approx(results.unexpected_percent, 0.1) == 100 - 23.3


def test_heuristic_proba_limits(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(german_credit_test_data, german_credit_model,
                                             'Not default', min_proba=0.4, max_proba=0.6)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 927
    assert pytest.approx(results.unexpected_percent, 0.1) == 92.7


def test_heuristic_pass_fail(german_credit_test_data, german_credit_model):
    assert _test_heuristic(german_credit_test_data, german_credit_model, 0.3)
    assert not _test_heuristic(german_credit_test_data, german_credit_model, 0.2)




def test_heuristic_filtered(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(
        german_credit_test_data.head(10),
        german_credit_model,
        classification_label='Default'
    )

    assert results.element_count == 10
    assert results.missing_count == 0
    assert results.unexpected_count == 4
    assert results.unexpected_percent == 40
