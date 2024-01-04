import pytest

from giskard.datasets.base import Dataset
from giskard.testing.tests.performance import (
    test_accuracy,
    test_auc,
    test_diff_accuracy,
    test_diff_f1,
    test_diff_precision,
    test_diff_recall,
    test_f1,
    test_mae,
    test_precision,
    test_r2,
    test_recall,
    test_rmse,
)


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_classification(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    dataset.df = dataset.df.head(20)

    predictions = model.predict(dataset)
    failed_series = predictions.prediction != dataset.df[dataset.target]
    benchmark_failed_idx = list(dataset.df.index.get_indexer_for(failed_series[failed_series].index))

    result = test_auc(model, dataset, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx

    result = test_recall(model, dataset, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx

    result = test_accuracy(model, dataset, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx

    result = test_precision(model, dataset, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx

    result = test_f1(model, dataset, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx


@pytest.mark.parametrize(
    "model,dataset",
    [("linear_regression_diabetes", "diabetes_dataset_with_target")],
)
def test_regression(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    dataset.df = dataset.df.head(20)
    df = dataset.df.head(20).copy()
    debug_percent_rows = 0.3

    predictions = model.predict(dataset).raw_prediction
    targets = dataset.df[dataset.target]
    df["metric"] = abs(predictions - targets)
    top_n = round(debug_percent_rows * len(df))
    benchmark_failed_idx = list(
        dataset.df.index.get_indexer_for(df.nlargest(top_n, "metric").drop("metric", axis=1).index)
    )

    result = test_mae(model, dataset, debug_percent_rows=debug_percent_rows, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx

    result = test_r2(model, dataset, debug_percent_rows=debug_percent_rows, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx

    result = test_rmse(model, dataset, debug_percent_rows=debug_percent_rows, debug=True).execute()
    failed_ds = result.output_ds[0]
    assert list(failed_ds.df.index) == benchmark_failed_idx


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_classification_diff(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    actual_dataset = Dataset(df=dataset.df.head(100), target=dataset.target, column_types=dataset.column_types)
    reference_dataset = Dataset(df=dataset.df.tail(100), target=dataset.target, column_types=dataset.column_types)

    result_actual = test_f1(model, actual_dataset, debug=True).execute()
    result_reference = test_f1(model, reference_dataset, debug=True).execute()
    benchmark_actual_failed = result_actual.output_ds[0]
    benchmark_reference_failed = result_reference.output_ds[0]

    # benchmark_failed_len = len(benchmark_failed)

    result = test_diff_f1(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    _assert_output_ds_diff_test(benchmark_actual_failed, benchmark_reference_failed, result)

    result = test_diff_accuracy(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    _assert_output_ds_diff_test(benchmark_actual_failed, benchmark_reference_failed, result)

    result = test_diff_recall(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    _assert_output_ds_diff_test(benchmark_actual_failed, benchmark_reference_failed, result)

    result = test_diff_precision(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    _assert_output_ds_diff_test(benchmark_actual_failed, benchmark_reference_failed, result)


def _assert_output_ds_diff_test(benchmark_actual_failed, benchmark_reference_failed, result):
    assert len(result.output_ds) == 2
    failed_reference_ds = result.output_ds[0]
    failed_actual_ds = result.output_ds[1]
    assert list(failed_actual_ds.df.index) == list(benchmark_actual_failed.df.index)
    assert list(failed_reference_ds.df.index) == list(benchmark_reference_failed.df.index)
