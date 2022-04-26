import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def _test_auc(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_auc(
        german_credit_data,
        german_credit_model,
        threshold=threshold,
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == 0.715
    return results.passed


def test_auc(german_credit_data, german_credit_model):
    assert _test_auc(german_credit_data, german_credit_model, 0.5)
    assert not _test_auc(german_credit_data, german_credit_model, 0.8)


def _test_f1(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_f1(
        german_credit_data,
        german_credit_model,
        threshold=threshold,
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == 0.602
    return results.passed


def test_f1(german_credit_data, german_credit_model):
    assert _test_f1(german_credit_data, german_credit_model, 0.6)
    assert not _test_f1(german_credit_data, german_credit_model, 0.7)


def _test_precision(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_precision(
        german_credit_data,
        german_credit_model,
        threshold=threshold,
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == 0.690
    return results.passed


def test_precision(german_credit_data, german_credit_model):
    assert _test_precision(german_credit_data, german_credit_model, 0.6)
    assert not _test_precision(german_credit_data, german_credit_model, 0.7)


def _test_recall(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_recall(
        german_credit_data,
        german_credit_model,
        threshold=threshold,
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == 0.533
    return results.passed


def test_recall(german_credit_data, german_credit_model):
    assert _test_recall(german_credit_data, german_credit_model, 0.5)
    assert not _test_recall(german_credit_data, german_credit_model, 0.6)


def _test_accuracy(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_accuracy(
        german_credit_data,
        german_credit_model,
        threshold=threshold,
        target='default'
    )

    assert results.element_count == 1000
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == 0.788
    return results.passed


def test_accuracy(german_credit_data, german_credit_model):
    assert _test_accuracy(german_credit_data, german_credit_model, 0.7)
    assert not _test_accuracy(german_credit_data, german_credit_model, 0.8)


def _test_neg_rmse(diabetes_dataset_with_target, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_neg_rmse(
        diabetes_dataset_with_target,
        linear_regression_diabetes,
        threshold=threshold,
        target='target'
    )

    assert results.element_count == 442
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == -2860.970
    return results.passed


def test_neg_rmse(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_neg_rmse(diabetes_dataset_with_target, linear_regression_diabetes, -2861)
    assert not _test_neg_rmse(diabetes_dataset_with_target, linear_regression_diabetes, -2860)


def _test_neg_mae(diabetes_dataset_with_target, linear_regression_diabetes, threshold=-44):
    tests = GiskardTestFunctions()
    results = tests.performance.test_neg_mae(
        diabetes_dataset_with_target,
        linear_regression_diabetes,
        threshold=threshold,
        target='target'
    )

    assert results.element_count == 442
    assert results.missing_count == 0
    assert pytest.approx(results.metric, 0.001) == -43.302
    return results.passed


def test_neg_mae(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_neg_mae(diabetes_dataset_with_target, linear_regression_diabetes, -44)
    assert not _test_neg_mae(diabetes_dataset_with_target, linear_regression_diabetes, -43)


def _test_r2(diabetes_dataset_with_target, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    tests.performance.test_r2(
        diabetes_dataset_with_target,
        linear_regression_diabetes,
        threshold=threshold,
        target='target'
    )

    assert len(tests.tests_results) == 1
    test_execution = tests.tests_results[0]
    result = test_execution.result
    assert test_execution.name == 'test_r2'
    assert pytest.approx(result.metric, 0.001) == 0.063
    return result.passed


def test_r2(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_r2(diabetes_dataset_with_target, linear_regression_diabetes, 0.062)
    assert not _test_r2(diabetes_dataset_with_target, linear_regression_diabetes, 0.064)


def _test_diff_accuracy(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    tests.performance.test_diff_accuracy(
        german_credit_data,
        german_credit_model,
        filter_1=german_credit_data[german_credit_data.sex == 'male'].index,
        filter_2=german_credit_data[german_credit_data.sex == 'female'].index,
        threshold=threshold,
        target='default'
    )
    assert len(tests.tests_results) == 1
    test_execution = tests.tests_results[0]
    result = test_execution.result
    assert test_execution.name == 'test_diff_accuracy'
    assert pytest.approx(result.metric, 0.001) == 0.0368
    return result.passed


def test_diff_accuracy(german_credit_data, german_credit_model):
    assert _test_diff_accuracy(german_credit_data, german_credit_model, 0.04)
    assert not _test_diff_accuracy(german_credit_data, german_credit_model, 0.02)


def _test_diff_f1(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_f1(
        german_credit_data,
        german_credit_model,
        filter_1=german_credit_data[german_credit_data.sex == 'male'].index,
        filter_2=german_credit_data[german_credit_data.sex == 'female'].index,
        threshold=threshold,
        target='default'
    )
    assert pytest.approx(result.metric, 0.001) == 0.14
    return result.passed


def test_diff_f1(german_credit_data, german_credit_model):
    assert _test_diff_f1(german_credit_data, german_credit_model, 0.15)
    assert not _test_diff_f1(german_credit_data, german_credit_model, 0.13)


def _test_diff_recall(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_recall(
        german_credit_data,
        german_credit_model,
        filter_1=german_credit_data[german_credit_data.sex == 'male'].index,
        filter_2=german_credit_data[german_credit_data.sex == 'female'].index,
        threshold=threshold,
        target='default'
    )
    assert pytest.approx(result.metric, 0.001) == 0.2624
    return result.passed


def test_diff_recall(german_credit_data, german_credit_model):
    assert _test_diff_recall(german_credit_data, german_credit_model, 0.263)
    assert not _test_diff_recall(german_credit_data, german_credit_model, 0.262)


def _test_diff_precision(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_precision(
        german_credit_data,
        german_credit_model,
        filter_1=german_credit_data[german_credit_data.sex == 'male'].index,
        filter_2=german_credit_data[german_credit_data.sex == 'female'].index,
        threshold=threshold,
        target='default'
    )
    assert pytest.approx(result.metric, 0.001) == 0.00266
    return result.passed


def test_diff_precision(german_credit_data, german_credit_model):
    assert _test_diff_precision(german_credit_data, german_credit_model, 0.00267)
    assert not _test_diff_precision(german_credit_data, german_credit_model, 0.00265)
