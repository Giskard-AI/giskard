import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def _test_heuristic(german_credit_test_data, german_credit_model, failed_threshold):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        classification_label=1,
        failed_threshold=failed_threshold)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 768
    assert results.unexpected_percent == 76.8
    return results.passed


def test_heuristic_opposite(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        0)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 1000 - 768
    assert pytest.approx(results.unexpected_percent, 0.1) == 100 - 76.8


def test_heuristic_proba_limits(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(german_credit_test_data, german_credit_model,
                                             0, min_proba=0.4, max_proba=0.6)

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert results.unexpected_count == 914
    assert pytest.approx(results.unexpected_percent, 0.1) == 91.4


def test_heuristic_pass(german_credit_test_data, german_credit_model):
    assert _test_heuristic(german_credit_test_data, german_credit_model, 0.8)


def test_heuristic_fail(german_credit_test_data, german_credit_model):
    assert not _test_heuristic(german_credit_test_data, german_credit_model, 0.5)


def test_heuristic_mask(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_heuristic(
        german_credit_test_data,
        german_credit_model,
        classification_label=1,
        mask=list(range(10))
    )

    assert results.element_count == 10
    assert results.missing_count == 0
    assert results.unexpected_count == 7
    assert results.unexpected_percent == 70
