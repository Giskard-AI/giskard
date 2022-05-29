import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def _test_heuristic(german_credit_test_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        slice_df=german_credit_test_data[:len(german_credit_test_data) // 2],
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[1],
        threshold=threshold
    )

    assert results.slice_nb_rows == 500
    assert round(results.metric, 2) == 0.80
    return results.passed


def test_heuristic_opposite(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        slice_df=german_credit_test_data[:len(german_credit_test_data) // 2],
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[0],
        threshold=0.5
    )

    assert results.slice_nb_rows == 500
    assert round(results.metric, 2) == round(1 - 0.80, 2)


def test_right_label(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        slice_df=german_credit_test_data[:len(german_credit_test_data) // 2],
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[1],
        threshold=0.5
    )

    assert results.slice_nb_rows == 500
    assert round(results.metric, 2) == 0.80
    assert results.passed


def test_heuristic_pass_fail(german_credit_test_data, german_credit_model):
    assert _test_heuristic(german_credit_test_data, german_credit_model, 0.7)
    assert not _test_heuristic(german_credit_test_data, german_credit_model, 0.9)


def test_heuristic_filtered(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        slice_df=german_credit_test_data.head(10),
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[0],
        threshold=0.5
      )

    assert results.slice_nb_rows == 10
    assert round(results.metric, 2) == 0.40

