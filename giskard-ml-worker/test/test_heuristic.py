import pytest

from giskard.ml_worker.testing.functions import GiskardTestFunctions


@pytest.mark.parametrize('data,model,label,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0, 0.1, 0.20, 500),
                          ('german_credit_data', 'german_credit_model', 1, 0.5, 0.80, 500),
                          ('enron_data', 'enron_model', 0, 0.1, 0.32, 25)])
def test_heuristic(data, model, threshold, label, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    results = tests.heuristic.test_right_label(
        actual_slice=data.slice(lambda df: df.head(len(df) // 2)),
        model=model,
        classification_label=model.classification_labels[label],
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize('data,model,label,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0, 0.3, 0.40, 10),
                          ('german_credit_data', 'german_credit_model', 1, 0.5, 0.60, 10),
                          ('enron_data', 'enron_model', 0, 0.01, 0.1, 10)])
def test_heuristic_filtered(data, model, threshold, label, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    results = tests.heuristic.test_right_label(
        actual_slice=data.slice(lambda df: df.head(10)),
        model=model,
        classification_label=model.classification_labels[label],
        threshold=threshold
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize('data,model,label,threshold,expected_metric,actual_slices_size',
                         [('german_credit_data', 'german_credit_model', 0, 0.1, 0.34, 500),
                          ('german_credit_data', 'german_credit_model', 1, 0.1, 0.34, 500),
                          ('enron_data', 'enron_model', 0, 0.1, 0.32, 25)])
def test_output_in_range_clf(data, model, threshold, label, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    results = tests.heuristic.test_output_in_range(
        actual_slice=data.slice(lambda df: df.head(len(df) // 2)),
        model=model,
        classification_label=model.classification_labels[label],
        min_range=0.3,
        max_range=0.7,
        threshold=threshold,
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize('data,model,threshold,expected_metric,actual_slices_size',
                         [('diabetes_dataset_with_target', 'linear_regression_diabetes', 0.1, 0.28, 221)])
def test_output_in_range_reg(data, model, threshold, expected_metric, actual_slices_size, request):
    tests = GiskardTestFunctions()
    data = request.getfixturevalue(data)
    results = tests.heuristic.test_output_in_range(
        actual_slice=data.slice(lambda df: df.head(len(df) // 2)),
        model=request.getfixturevalue(model),
        min_range=100,
        max_range=150,
        threshold=threshold,
    )

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed
