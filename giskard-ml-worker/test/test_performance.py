import pytest

from ml_worker.testing.functions import GiskardTestFunctions


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0.5, 0.85, 1000),
                          ('enron_data', 'enron_model', 0.5, 0.67, 50)])
def test_f1(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_f1(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size

    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0.5, 0.71, 1000),
                          ('enron_data', 'enron_model', 0.5, 0.94, 50)])
def test_auc(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_auc(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0.5, 0.81, 1000),
                          ('enron_data', 'enron_model', 0.5, 0.72, 50)])
def test_precision(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_precision(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0.5, 0.89, 1000),
                          ('enron_data', 'enron_model', 0.5, 0.66, 50)])
def test_recall(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_recall(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0.5, 0.78, 1000),
                          ('enron_data', 'enron_model', 0.5, 0.76, 50)])
def test_accuracy(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_accuracy(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('diabetes_dataset_with_target', 'linear_regression_diabetes', 54, 53.49, 442)])
def test_rmse(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_rmse(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('diabetes_dataset_with_target', 'linear_regression_diabetes', 44, 43.3, 442)])
def test_mae(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_mae(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('diabetes_dataset_with_target', 'linear_regression_diabetes', 0.4, 0.52, 442)])
def test_r2(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    results = tests.performance.test_r2(
        actual_slice=request.getfixturevalue(data),
        model=request.getfixturevalue(model),
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert type(results.output_df) is bytes
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('german_credit_data', 'german_credit_model', 0.08, 0.05)])
def test_diff_f1(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_f1(
        actual_slice=data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=data.slice(lambda df: df[df.sex == 'female']),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('german_credit_data', 'german_credit_model', 0.2, 0.04)])
def test_diff_accuracy(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_accuracy(
        actual_slice=data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=data.slice(lambda df: df[df.sex == 'female']),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('german_credit_data', 'german_credit_model', 0.2, 0.1)])
def test_diff_recall(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_recall(
        actual_slice=data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=data.slice(lambda df: df[df.sex == 'female']),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('german_credit_data', 'german_credit_model', 0.2, 0.01)])
def test_diff_precision(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_precision(
        actual_slice=data.slice(lambda df: df[df.sex == 'male']),
        reference_slice=data.slice(lambda df: df[df.sex == 'female']),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('diabetes_dataset_with_target', 'linear_regression_diabetes', 0.1, 0.08, 207)])
def test_diff_rmse(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_rmse(
        actual_slice=data.slice(lambda df: df[df.sex > 0]),
        reference_slice=data.slice(lambda df: df[df.sex < 0]),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert result.actual_slices_size[0] == actual_slices_size
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('german_credit_data', 'german_credit_model', 0.1, 0.03),
                          ('enron_data', 'enron_model', 0.5, 0.17)])
def test_diff_reference_actual_f1(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_reference_actual_f1(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('german_credit_data', 'german_credit_model', 0.1, 0.03),
                          ('enron_data', 'enron_model', 0.5, 0.00)])
def test_diff_reference_actual_accuracy(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_reference_actual_accuracy(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric',
                         [('diabetes_dataset_with_target', 'linear_regression_diabetes', 0.1, 0.02)])
def test_diff_reference_actual_rmse(data, model, threshold, expected_metric, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    result = tests.performance.test_diff_reference_actual_rmse(
        reference_slice=data.slice(lambda df: df.head(len(df) // 2)),
        actual_slice=data.slice(lambda df: df.tail(len(df) // 2)),
        model=request.getfixturevalue(model),
        threshold=threshold
    )
    assert round(result.metric, 2) == expected_metric
    assert type(result.output_df) is bytes
    assert result.passed