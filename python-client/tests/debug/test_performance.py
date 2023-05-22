from giskard.ml_worker.testing.tests.performance import test_auc, test_recall, test_accuracy, test_precision, test_f1
from giskard.ml_worker.testing.tests.performance import test_mae, test_r2, test_rmse
from giskard.ml_worker.testing.tests.performance import test_diff_f1, test_diff_accuracy, test_diff_recall, \
    test_diff_precision
from giskard.datasets.base import Dataset
import pytest
import pandas as pd


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
    benchmark_failed_idx = list(failed_series[failed_series].index.values)

    result = test_auc(model, dataset, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    result = test_recall(model, dataset, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    result = test_accuracy(model, dataset, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    result = test_precision(model, dataset, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    result = test_f1(model, dataset, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx


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
    df['metric'] = abs(predictions - targets)
    top_n = round(debug_percent_rows * len(df))
    benchmark_failed_idx = list(df.nlargest(top_n, 'metric').drop('metric', axis=1).index.values)

    result = test_mae(model, dataset, debug_percent_rows=debug_percent_rows, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    result = test_r2(model, dataset, debug_percent_rows=debug_percent_rows, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    result = test_rmse(model, dataset, debug_percent_rows=debug_percent_rows, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_classification_diff(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    actual_dataset = Dataset(df=dataset.df.head(100),
                             target=dataset.target,
                             column_types=dataset.column_types)
    reference_dataset = Dataset(df=dataset.df.tail(100),
                                target=dataset.target,
                                column_types=dataset.column_types)

    result_actual = test_f1(model, actual_dataset, debug=True).execute()
    result_reference = test_f1(model, reference_dataset, debug=True).execute()
    benchmark_failed = pd.concat([result_actual.output_df.df,
                                  result_reference.output_df.df], ignore_index=True)
    benchmark_failed_len = len(benchmark_failed)

    result = test_diff_f1(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    assert len(result.output_df.df) == benchmark_failed_len

    result = test_diff_accuracy(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    assert len(result.output_df.df) == benchmark_failed_len

    result = test_diff_recall(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    assert len(result.output_df.df) == benchmark_failed_len

    result = test_diff_precision(model, actual_dataset, reference_dataset, debug=True, threshold=0.01).execute()
    assert len(result.output_df.df) == benchmark_failed_len
