import pytest

from ml_worker.testing.functions import GiskardTestFunctions


def _test_auc(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_auc(
        actual_slice=german_credit_data,
        model=german_credit_model,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 1000
    assert round(results.metric, 2) == 0.71
    return results.passed


def test_auc(german_credit_data, german_credit_model):
    assert _test_auc(german_credit_data, german_credit_model, 0.5)
    assert not _test_auc(german_credit_data, german_credit_model, 0.8)


def _test_f1(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_f1(
        actual_slice=german_credit_data,
        model=german_credit_model,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 1000

    assert round(results.metric, 2) == 0.85
    return results.passed


def test_f1(german_credit_data, german_credit_model):
    assert _test_f1(german_credit_data, german_credit_model, 0.2)
    assert not _test_f1(german_credit_data, german_credit_model, 0.9)


def _test_precision(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_precision(
        actual_slice=german_credit_data,
        model=german_credit_model,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 1000
    assert round(results.metric, 2) == 0.81
    return results.passed


def test_precision(german_credit_data, german_credit_model):
    assert _test_precision(german_credit_data, german_credit_model, 0.2)
    assert not _test_precision(german_credit_data, german_credit_model, 0.9)


def _test_recall(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_recall(
        actual_slice=german_credit_data,
        model=german_credit_model,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 1000
    assert round(results.metric, 2) == 0.89
    return results.passed


def test_recall(german_credit_data, german_credit_model):
    assert _test_recall(german_credit_data, german_credit_model, 0.4)
    assert not _test_recall(german_credit_data, german_credit_model, 0.9)


def _test_accuracy(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_accuracy(
        actual_slice=german_credit_data,
        model=german_credit_model,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 1000
    assert round(results.metric, 2) == 0.78
    return results.passed


def test_accuracy(german_credit_data, german_credit_model):
    assert _test_accuracy(german_credit_data, german_credit_model, 0.2)
    assert not _test_accuracy(german_credit_data, german_credit_model, 0.9)


def _test_rmse(diabetes_dataset_with_target, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    results = tests.performance.test_rmse(
        actual_slice=diabetes_dataset_with_target,
        model=linear_regression_diabetes,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 53.49
    return results.passed


def test_rmse(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_rmse(diabetes_dataset_with_target, linear_regression_diabetes, 52)
    assert not _test_rmse(diabetes_dataset_with_target, linear_regression_diabetes, 54)


def _test_mae(diabetes_dataset_with_target, linear_regression_diabetes, threshold=44):
    tests = GiskardTestFunctions()
    results = tests.performance.test_mae(
        actual_slice=diabetes_dataset_with_target,
        model=linear_regression_diabetes,
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 442
    assert round(results.metric, 2) == 43.3
    return results.passed


def test_mae(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_mae(diabetes_dataset_with_target, linear_regression_diabetes, 43)
    assert not _test_mae(diabetes_dataset_with_target, linear_regression_diabetes, 44)


def _test_r2(diabetes_dataset_with_target, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    tests.performance.test_r2(
        actual_slice=diabetes_dataset_with_target,
        model=linear_regression_diabetes,
        threshold=threshold
    )

    assert len(tests.tests_results) == 1
    test_execution = tests.tests_results[0]
    result = test_execution.result
    assert test_execution.name == 'test_r2'
    assert round(result.metric, 2) == 0.52
    return result.passed


def test_r2(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_r2(diabetes_dataset_with_target, linear_regression_diabetes, 0.062)
    assert not _test_r2(diabetes_dataset_with_target, linear_regression_diabetes, 0.6)


def _test_diff_accuracy(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    tests.performance.test_diff_accuracy(
        actual_slice=german_credit_data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=german_credit_data.slice(lambda df: df[df.sex == 'female']),
        model=german_credit_model,
        threshold=threshold
    )
    assert len(tests.tests_results) == 1
    test_execution = tests.tests_results[0]
    result = test_execution.result
    assert test_execution.name == 'test_diff_accuracy'
    assert round(result.metric, 2) == 0.04
    return result.passed


def test_diff_accuracy(german_credit_data, german_credit_model):
    assert _test_diff_accuracy(german_credit_data, german_credit_model, 0.2)
    assert not _test_diff_accuracy(german_credit_data, german_credit_model, 0.01)


def _test_diff_f1(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_f1(
        actual_slice=german_credit_data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=german_credit_data.slice(lambda df: df[df.sex == 'female']),
        model=german_credit_model,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.05
    return result.passed


def test_diff_f1(german_credit_data, german_credit_model):
    assert _test_diff_f1(german_credit_data, german_credit_model, 0.08)
    assert not _test_diff_f1(german_credit_data, german_credit_model, 0.02)


def _test_diff_recall(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_recall(
        actual_slice=german_credit_data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=german_credit_data.slice(lambda df: df[df.sex == 'female']),
        model=german_credit_model,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.09
    return result.passed


def test_diff_recall(german_credit_data, german_credit_model):
    assert _test_diff_recall(german_credit_data, german_credit_model, 0.4)
    assert not _test_diff_recall(german_credit_data, german_credit_model, 0.01)


def _test_diff_precision(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_precision(
        actual_slice=german_credit_data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=german_credit_data.slice(lambda df: df[df.sex == 'female']),
        model=german_credit_model,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.01
    return result.passed


def test_diff_precision(german_credit_data, german_credit_model):
    assert _test_diff_precision(german_credit_data, german_credit_model, 0.06)
    assert not _test_diff_precision(german_credit_data, german_credit_model, 0)


def _test_diff_rmse(diabetes_dataset_with_target, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_rmse(
        actual_slice=diabetes_dataset_with_target.slice(lambda df: df[df.sex > 0]),
        reference_slice=diabetes_dataset_with_target.slice(lambda df: df[df.sex < 0]),
        model=linear_regression_diabetes,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.08
    return result.passed


def test_diff_rmse(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_diff_rmse(diabetes_dataset_with_target, linear_regression_diabetes, 1)
    assert not _test_diff_rmse(diabetes_dataset_with_target, linear_regression_diabetes, 0.05)


def _test_diff_reference_actual_f1(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_reference_actual_f1(
        reference_slice=german_credit_data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=german_credit_data.slice(lambda df: df.tail(len(df) // 2)),
        model=german_credit_model,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.03
    return result.passed


def test_diff_reference_actual_f1(german_credit_data, german_credit_model):
    assert _test_diff_reference_actual_f1(german_credit_data, german_credit_model, 0.4)
    assert not _test_diff_reference_actual_f1(german_credit_data, german_credit_model, 0.01)


def _test_diff_reference_actual_accuracy(german_credit_data, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_reference_actual_accuracy(
        reference_slice=german_credit_data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=german_credit_data.slice(lambda df: df.tail(len(df) // 2)),
        model=german_credit_model,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.03
    return result.passed


def test_diff_reference_actual_accuracy(german_credit_data, german_credit_model):
    assert _test_diff_reference_actual_accuracy(german_credit_data, german_credit_model, 0.4)
    assert not _test_diff_reference_actual_accuracy(german_credit_data, german_credit_model, 0.01)


def _test_diff_reference_actual_rmse(diabetes_dataset_with_target, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    result = tests.performance.test_diff_reference_actual_rmse(
        reference_slice=diabetes_dataset_with_target.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=diabetes_dataset_with_target.slice(lambda df: df.tail(len(df) // 2)),
        model=linear_regression_diabetes,
        threshold=threshold
    )
    assert round(result.metric, 2) == 0.02
    return result.passed


def test_diff_reference_actual_rmse(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_diff_reference_actual_rmse(diabetes_dataset_with_target, linear_regression_diabetes, 0.4)
    assert not _test_diff_reference_actual_rmse(diabetes_dataset_with_target, linear_regression_diabetes, 0.01)
