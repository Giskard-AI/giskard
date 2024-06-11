import re

import numpy as np
import pandas as pd
import pytest
import sklearn

import giskard.testing.tests.performance as performance
from giskard.registry.slicing_function import SlicingFunction, slicing_function
from giskard.testing.utils.utils import Direction


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_model", "german_credit_data", 0.5, 0.85, 1000),
        ("enron_model", "enron_data", 0.5, 0.76, 50),
    ],
)
def test_f1(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_f1(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_model", "german_credit_data", 0.5, 0.83, 1000),
        ("enron_model", "enron_data", 0.5, 0.94, 50),
    ],
)
def test_auc(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_auc(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("enron_model", "enron_data", 0.5, 1, 7)],
)
def test_auc_with_unique_target_no_exception(model, data, threshold, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    results = performance.test_auc(
        model=request.getfixturevalue(model),
        dataset=data.slice(SlicingFunction(lambda df: df.drop_duplicates("Target"), row_level=False)),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("enron_model", "enron_data", 0.5, 1, 7)],
)
def test_auc_with_unique_target_raise_exception(model, data, threshold, expected_metric, actual_slices_size, request):
    with pytest.raises(AssertionError) as e:
        data = request.getfixturevalue(data)
        performance.test_auc(
            model=request.getfixturevalue(model),
            dataset=data.slice(SlicingFunction(lambda df: df.drop_duplicates("Target").head(), row_level=False)),
            threshold=threshold,
        ).execute()

    assert "Predicted classes don't exist in the dataset" in str(e.value)


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_model", "german_credit_data", 0.5, 0.81, 1000),
        ("enron_model", "enron_data", 0.5, 0.76, 50),
    ],
)
def test_precision(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_precision(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_model", "german_credit_data", 0.5, 0.89, 1000),
        ("enron_model", "enron_data", 0.5, 0.76, 50),
    ],
)
def test_recall(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_recall(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_model", "german_credit_data", 0.5, 0.15, 1000),
    ],
)
def test_brier(model, data, threshold, expected_metric, actual_slices_size, request):
    giskard_model = request.getfixturevalue(model)
    giskard_dataset = request.getfixturevalue(data)
    results = performance.test_brier(model=giskard_model, dataset=giskard_dataset, threshold=threshold).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed
    sklearn_metric = sklearn.metrics.brier_score_loss(
        giskard_dataset.df[giskard_dataset.target],
        np.array(giskard_model.predict(giskard_dataset).raw[:, 1]),
        pos_label=giskard_model.classification_labels[1],
    )
    assert results.metric == sklearn_metric


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_model", "german_credit_data", 0.5, 0.78, 1000),
        ("enron_model", "enron_data", 0.5, 0.76, 50),
    ],
)
def test_accuracy(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_accuracy(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("linear_regression_diabetes", "diabetes_dataset_with_target", 54, 53.49, 442)],
)
def test_rmse(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_rmse(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("linear_regression_diabetes", "diabetes_dataset_with_target", 54**2, 2860.97, 442)],
)
def test_mse(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_mse(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert results.metric == pytest.approx(expected_metric, abs=1e-2)
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("linear_regression_diabetes", "diabetes_dataset_with_target", 44, 43.3, 442)],
)
def test_mae(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_mae(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("linear_regression_diabetes", "diabetes_dataset_with_target", 0.4, 0.52, 442)],
)
def test_r2(model, data, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_r2(
        model=request.getfixturevalue(model), dataset=request.getfixturevalue(data), threshold=threshold
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric",
    [("german_credit_model", "german_credit_data", 0.08, 0.05)],
)
def test_diff_f1(model, data, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_f1(
        model=request.getfixturevalue(model),
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        threshold=threshold,
    ).execute()

    assert round(result.metric, 2) == expected_metric
    assert result.passed

    # Test increasing with positive threshold (should fail)
    result = performance.test_diff_f1(
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        model=request.getfixturevalue(model),
        threshold=threshold,
        direction=Direction.Increasing,
    ).execute()

    assert round(result.metric, 2) == -expected_metric
    assert not result.passed

    # Test increasing with negative threshold (should pass)
    result = performance.test_diff_f1(
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        model=request.getfixturevalue(model),
        threshold=-threshold,
        direction=Direction.Increasing,
    ).execute()

    assert round(result.metric, 2) == -expected_metric
    assert result.passed

    # Test decreasing with negative threshold (should pass)
    result = performance.test_diff_f1(
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        model=request.getfixturevalue(model),
        threshold=threshold,
        direction=Direction.Decreasing,
    ).execute()

    assert round(result.metric, 2) == -expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric",
    [("german_credit_model", "german_credit_data", 0.2, 0.04)],
)
def test_diff_accuracy(model, data, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_accuracy(
        model=request.getfixturevalue(model),
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        threshold=threshold,
    ).execute()

    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.skip(reason="TODO: fixme")
@pytest.mark.parametrize(
    "test_fn_name,model,data,threshold,expected_metric",
    [
        ("test_diff_accuracy", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_f1", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_precision", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_recall", "german_credit_data", "german_credit_always_default_model", 0, 0),
    ],
)
def test_diff_always_default(test_fn_name, data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)

    test_fn = getattr(performance, test_fn_name)

    result = test_fn(
        actual_slice=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        reference_slice=data.slice(
            SlicingFunction(lambda df: df[(df.sex == "female") & (df.default == "Not default")], row_level=False)
        ),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert round(result.metric, 2) == expected_metric

    assert not result.passed
    assert len(result.messages) == 1
    assert re.match(
        "^Unable to calculate performance difference: the." "*inside the reference_dataset is equal to zero$",
        result.messages[0].text,
    )


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric",
    [("german_credit_model", "german_credit_data", 0.2, 0.1)],
)
def test_diff_recall(model, data, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_recall(
        model=request.getfixturevalue(model),
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric",
    [("german_credit_model", "german_credit_data", 0.2, 0.01)],
)
def test_diff_precision(model, data, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_precision(
        model=request.getfixturevalue(model),
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "male"], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex == "female"], row_level=False)),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "model,data,threshold,expected_metric,actual_slices_size",
    [("linear_regression_diabetes", "diabetes_dataset_with_target", 0.1, -0.08, 207)],
)
def test_diff_rmse(model, data, threshold, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_rmse(
        model=request.getfixturevalue(model),
        actual_dataset=data.slice(SlicingFunction(lambda df: df[df.sex > 0], row_level=False)),
        reference_dataset=data.slice(SlicingFunction(lambda df: df[df.sex < 0], row_level=False)),
        threshold=threshold,
    ).execute()
    assert result.actual_slices_size[0] == actual_slices_size
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("german_credit_data", "german_credit_model", 0.5, 0.85, 1000)],
)
def test_f1_empty_slice(data, model, threshold, expected_metric, actual_slices_size, request):
    @slicing_function
    def my_slicing_function(row: pd.Series):
        return row["age"] > 100

    with pytest.raises(ValueError, match="The sliced dataset in test_f1 is empty."):
        performance.test_f1(
            dataset=request.getfixturevalue(data),
            model=request.getfixturevalue(model),
            slicing_function=my_slicing_function,
            threshold=threshold,
        ).execute()
