import re

import pytest

import giskard.ml_worker.testing.tests.performance as performance


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0.5, 0.85, 1000),
        ("enron_data", "enron_model", 0.5, 0.67, 50),
    ],
)
def test_f1(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_f1(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size

    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0.5, 0.71, 1000),
        ("enron_data", "enron_model", 0.5, 0.94, 50),
    ],
)
def test_auc(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_auc(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("enron_data", "enron_model", 0.5, 1, 7)],
)
def test_auc_with_unique_target_no_exception(data, model, threshold, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    results = performance.test_auc(
        actual_slice=data.slice(lambda df: df.drop_duplicates("Target"), row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("enron_data", "enron_model", 0.5, 1, 7)],
)
def test_auc_with_unique_target_raise_exception(data, model, threshold, expected_metric, actual_slices_size, request):
    with pytest.raises(AssertionError) as e:
        data = request.getfixturevalue(data)
        performance.test_auc(
            actual_slice=data.slice(lambda df: df.drop_duplicates("Target").head(), row_level=False),
            model=request.getfixturevalue(model),
            threshold=threshold,
        ).execute()

    assert "Predicted classes don't exist in the dataset" in str(e.value)


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0.5, 0.81, 1000),
        ("enron_data", "enron_model", 0.5, 0.72, 50),
    ],
)
def test_precision(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_precision(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0.5, 0.89, 1000),
        ("enron_data", "enron_model", 0.5, 0.66, 50),
    ],
)
def test_recall(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_recall(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0.5, 0.78, 1000),
        ("enron_data", "enron_model", 0.5, 0.76, 50),
    ],
)
def test_accuracy(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_accuracy(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 54, 53.49, 442)],
)
def test_rmse(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_rmse(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 44, 43.3, 442)],
)
def test_mae(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_mae(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0.4, 0.52, 442)],
)
def test_r2(data, model, threshold, expected_metric, actual_slices_size, request):
    results = performance.test_r2(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("german_credit_data", "german_credit_model", 0.08, 0.05)],
)
def test_diff_f1(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_f1(
        actual_slice=data.slice(lambda df: df[df.sex == "male"], row_level=False),
        reference_slice=data.slice(lambda df: df[df.sex == "female"], row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("german_credit_data", "german_credit_model", 0.2, 0.04)],
)
def test_diff_accuracy(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_accuracy(
        actual_slice=data.slice(lambda df: df[df.sex == "male"], row_level=False),
        reference_slice=data.slice(lambda df: df[df.sex == "female"], row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.skip(reason="TODO: fixme")
@pytest.mark.parametrize(
    "test_fn_name,data,model,threshold,expected_metric",
    [
        ("test_diff_accuracy", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_f1", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_precision", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_recall", "german_credit_data", "german_credit_always_default_model", 0, 0),
        ("test_diff_reference_actual_f1", "german_credit_data", "german_credit_always_default_model", 0, 0),
    ],
)
def test_diff_always_default(test_fn_name, data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)

    test_fn = getattr(performance, test_fn_name)

    result = test_fn(
        actual_slice=data.slice(lambda df: df[df.sex == "male"], row_level=False),
        reference_slice=data.slice(lambda df: df[(df.sex == "female") & (df.default == "Not default")], row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()

    assert round(result.metric, 2) == expected_metric

    assert not result.passed
    assert len(result.messages) == 1
    assert re.match(
        "^Unable to calculate performance difference: the." "*inside the reference_slice is equal to zero$",
        result.messages[0].text,
    )


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("german_credit_data", "german_credit_model", 0.2, 0.1)],
)
def test_diff_recall(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_recall(
        actual_slice=data.slice(lambda df: df[df.sex == "male"], row_level=False),
        reference_slice=data.slice(lambda df: df[df.sex == "female"], row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("german_credit_data", "german_credit_model", 0.2, 0.01)],
)
def test_diff_precision(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_precision(
        actual_slice=data.slice(lambda df: df[df.sex == "male"], row_level=False),
        reference_slice=data.slice(lambda df: df[df.sex == "female"], row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0.1, 0.08, 207)],
)
def test_diff_rmse(data, model, threshold, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_rmse(
        actual_slice=data.slice(lambda df: df[df.sex > 0], row_level=False),
        reference_slice=data.slice(lambda df: df[df.sex < 0], row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()
    assert result.actual_slices_size[0] == actual_slices_size
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [
        ("german_credit_data", "german_credit_model", 0.1, 0.03),
        ("enron_data", "enron_model", 0.5, 0.17),
    ],
)
def test_diff_reference_actual_f1(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_reference_actual_f1(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2), row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [
        ("german_credit_data", "german_credit_model", 0.1, 0.03),
        ("enron_data", "enron_model", 0.5, 0.00),
    ],
)
def test_diff_reference_actual_accuracy(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_reference_actual_accuracy(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2), row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0.1, 0.02)],
)
def test_diff_reference_actual_rmse(data, model, threshold, expected_metric, request):
    data = request.getfixturevalue(data)
    result = performance.test_diff_reference_actual_rmse(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2), row_level=False),
        model=request.getfixturevalue(model),
        threshold=threshold,
    ).execute()
    assert round(result.metric, 2) == expected_metric
    assert result.passed
