import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def test_auc(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_auc(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.5,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.715
    return results.passed


def test_auc_fail(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_auc(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.8,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.715
    return not results.passed


def test_f1(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_f1(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.5,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.602
    return results.passed


def test_f1_fail(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_f1(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.7,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.602
    return not results.passed


def test_precision(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_precision(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.5,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.690
    return results.passed


def test_precision_fail(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_precision(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.7,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.690
    return not results.passed


def test_recall(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_recall(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.5,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.533
    return results.passed


def test_recall_fail(german_credit_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.performance.test_recall(
        german_credit_data,
        german_credit_model,
        failed_threshold=0.6,
        classification_labels=[0, 1],
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == 0.533
    return not results.passed


def test_neg_rmse(diabetes_dataset_with_target, linear_regression_diabetes):
    tests = GiskardTestFunctions()
    results = tests.performance.test_neg_rmse(
        diabetes_dataset_with_target,
        linear_regression_diabetes,
        failed_threshold=0.6,
        target='target'
    )

    assert results.element_count == 442
    assert results.missing_count == 0
    assert pytest.approx(float(results.props.get('metric')), 0.001) == -2860.970
    return not results.passed
