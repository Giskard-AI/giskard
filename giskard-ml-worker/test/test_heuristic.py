from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.testing.functions import GiskardTestFunctions


def _test_heuristic(german_credit_test_data: GiskardDataset, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        actual_slice=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[1],
        threshold=threshold
    )

    assert results.actual_slices_size[0] == 500
    assert round(results.metric, 2) == 0.80
    return results.passed


def test_heuristic_opposite(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        actual_slice=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[0],
        threshold=0.5
    )

    assert results.actual_slices_size[0] == 500
    assert round(results.metric, 2) == round(1 - 0.80, 2)


def test_right_label(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        actual_slice=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[1],
        threshold=0.5
    )

    assert results.actual_slices_size[0] == 500
    assert round(results.metric, 2) == 0.80
    assert results.passed


def test_heuristic_pass_fail(german_credit_test_data, german_credit_model):
    assert _test_heuristic(german_credit_test_data, german_credit_model, 0.7)
    assert not _test_heuristic(german_credit_test_data, german_credit_model, 0.9)


def test_heuristic_filtered(german_credit_test_data, german_credit_model):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_right_label(
        actual_slice=german_credit_test_data.slice(lambda df: df.head(10)),
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[0],
        threshold=0.5
    )

    assert results.actual_slices_size[0] == 10
    assert round(results.metric, 2) == 0.40


def _test_output_in_range_clf(german_credit_test_data: GiskardDataset, german_credit_model, threshold):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_output_in_range(
        actual_slice=german_credit_test_data.slice(lambda df: df.head(len(df) // 2)),
        model=german_credit_model,
        classification_label=german_credit_model.classification_labels[1],
        min_range=0.3,
        max_range=0.7,
        threshold=threshold,
    )

    assert results.actual_slices_size[0] == 500
    assert round(results.metric, 2) == 0.34
    return results.passed


def test_output_in_range_clf(german_credit_test_data, german_credit_model):
    assert _test_output_in_range_clf(german_credit_test_data, german_credit_model, 0.2)
    assert not _test_output_in_range_clf(german_credit_test_data, german_credit_model, 0.9)


def _test_output_in_range_reg(diabetes_dataset_with_target: GiskardDataset, linear_regression_diabetes, threshold):
    tests = GiskardTestFunctions()
    results = tests.heuristic.test_output_in_range(
        actual_slice=diabetes_dataset_with_target.slice(lambda df: df.head(len(df) // 2)),
        model=linear_regression_diabetes,
        min_range=100,
        max_range=150,
        threshold=threshold,
    )

    assert results.actual_slices_size[0] == 221
    assert round(results.metric, 2) == 0.28
    return results.passed


def test_output_in_range_reg(diabetes_dataset_with_target, linear_regression_diabetes):
    assert _test_output_in_range_reg(diabetes_dataset_with_target, linear_regression_diabetes, 0.2)
    assert not _test_output_in_range_reg(diabetes_dataset_with_target, linear_regression_diabetes, 0.9)
