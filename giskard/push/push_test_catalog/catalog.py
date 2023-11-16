"""
This module defines various test functions that can be used with pushes.

The main functions are:

- if_underconfidence_rate_decrease: Custom test for underconfidence rate decrease  
- if_overconfidence_rate_decrease: Custom test for overconfidence rate decrease
- correct_example: Unit test for example correctness
- increase_probability: Test for increasing probability of ground truth label
- one_sample_overconfidence_test: One-sample test for overconfidence
- one_sample_underconfidence_test: One-sample test for underconfidence
- test_metamorphic_invariance_with_mad: Metamorphic test with mean absolute deviation

These test functions allow validating pushes and can be added to test suites.
"""
from typing import Any, Optional

from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.functions.transformation import mad_transformation
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.test_result import TestResult
from giskard.ml_worker.testing.utils import Direction, check_slice_not_empty
from giskard.models.base import BaseModel
from giskard.testing.tests.calibration import test_overconfidence_rate, test_underconfidence_rate
from giskard.testing.tests.metamorphic import test_metamorphic_invariance
from giskard.testing.tests.performance import _test_diff_prediction, test_f1, test_rmse


@test(name="Slicing RMSE difference", tags=["performance", "regression", "ground_truth", "push"])
def test_diff_rmse_push(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.1,
    direction: Direction = Direction.Decreasing,
):
    """
    Test for difference in RMSE between a slice and full dataset.

    Checks if the RMSE on a sliced subset of the data is significantly
    different from the full dataset based on a threshold and direction.

    Can be used with pushes to test if problematic slices have worse RMSE.

    Args:
        model: Model to test
        dataset: Full dataset
        slicing_function: Function to slice dataset
        threshold: Allowed RMSE difference
        direction: Whether slice RMSE should increase or decrease

    Returns:
        TestResult with pass/fail, slice sizes, RMSE diff, debug dataset
    """
    if slicing_function:
        test_name = "test_diff_rmse_push"
        actual_dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_rmse.test_fn,
        model,
        actual_dataset,
        dataset,
        threshold=threshold,
        direction=direction,
        test_name="RMSE",
    )


@test(name="Slicing f1 difference", tags=["performance", "classification", "ground_truth", "push"])
def test_diff_f1_push(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = -0.1,
    direction: Direction = Direction.Increasing,
):
    """
    Test for difference in F1 score between a slice and full dataset.

    Checks if the F1 score on a sliced subset of the data is significantly
    different from the full dataset based on a threshold and direction.

    Can be used with pushes to test if problematic slices have worse F1 score.

    Args:
        model: Model to test
        dataset: Full dataset
        slicing_function: Function to slice dataset
        threshold: Allowed F1 score difference
        direction: Whether slice F1 should increase or decrease

    Returns:
       TestResult with pass/fail, slice sizes, F1 diff, debug dataset
    """
    if slicing_function:
        test_name = "test_diff_f1_push"
        actual_dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_f1.test_fn,
        model,
        actual_dataset,
        dataset,
        threshold=threshold,
        direction=direction,
        test_name="f1",
    )


@test(name="If Underconfidence Decreases", tags=["custom"])
def if_underconfidence_rate_decrease(model: BaseModel, dataset: Dataset, rate: float):
    """
    Test if underconfidence rate decreases for model on dataset.

    Checks if the underconfidence rate for the model on the provided dataset
    is lower than the specified rate.

    Args:
        model: Model to test
        dataset: Dataset to test on
        rate: Target underconfidence rate to decrease from

    Returns:
        TestResult: Test result with pass/fail and underconfidence rate metric
    """
    new_rate = test_underconfidence_rate(model, dataset).metric
    return TestResult(passed=new_rate < rate, metric=new_rate - rate)


@test(name="If Overconfidence Decreases", tags=["custom"])
def if_overconfidence_rate_decrease(model: BaseModel, dataset: Dataset, rate: float):
    """
    Test if overconfidence rate decreases for model on dataset.

    Checks if the overconfidence rate for the model on the provided dataset
    is lower than the specified rate.

    Args:
        model: Model to test
        dataset: Dataset to test on
        rate: Target overconfidence rate to decrease from

    Returns:
        TestResult: Test result with pass/fail and overconfidence rate metric
    """
    new_rate = test_overconfidence_rate(model, dataset).metric
    return TestResult(passed=new_rate < rate, metric=new_rate - rate)


@test(name="Example Correctness", tags=["unit test", "custom"])
def correct_example(model: BaseModel, saved_example: Dataset, training_label: Any):
    """
    Test if model correctly predicts example.

    Checks if the model's prediction on the saved example matches the
    provided training label ground truth.

    Args:
        model: Model to test
        saved_example: Example dataset
        training_label: Ground truth label

    Returns:
        TestResult: Test result with pass/fail
    """
    prediction = model.predict(saved_example).prediction.values[0]
    return TestResult(passed=prediction == training_label, metric=prediction == training_label)


@test(name="Increase Probability", tags=["unit test", "custom"])
def increase_probability(model: BaseModel, saved_example: Dataset, training_label: Any, training_label_proba: Any):
    """
    Test if model probability for ground truth label increases.

    Checks if the predicted probability for the training label increases
    compared to the original training probability.

    Args:
        model: Model to test
        saved_example: Example dataset
        training_label: Ground truth label
        training_label_proba: Original probability

    Returns:
        TestResult: Test result with pass/fail and probability metric
    """
    proba = model.predict(saved_example).all_predictions[training_label].values[0]
    return TestResult(passed=proba > training_label_proba, metric=proba - training_label_proba)


@test(name="One-Sample Overconfidence test", tags=["one-sample test", "custom"])
def one_sample_overconfidence_test(model: BaseModel, saved_example: Dataset):
    """
    One-sample overconfidence test for example.

    Checks if the overconfidence rate for the model on the
    provided example is below a threshold.

    Args:
        model: Model to test
        saved_example: Example dataset

    Returns:
        TestResult: Test result with pass/fail and overconfidence rate metric
    """
    if model.is_classification:
        test_result = test_overconfidence_rate(model, saved_example).execute()
        return TestResult(passed=test_result.passed, metric=test_result.metric)


@test(name="One-Sample Underconfidence test", tags=["one-sample test", "custom"])
def one_sample_underconfidence_test(model: BaseModel, saved_example: Dataset):
    """
    One-sample underconfidence test for example.

    Checks if the underconfidence rate for the model on the
    provided example is below a threshold.

    Args:
        model: Model to test
        saved_example: Example dataset

    Returns:
        TestResult: Test result with pass/fail and underconfidence rate metric
    """
    if model.is_classification:
        test_result = test_underconfidence_rate(model, saved_example).execute()
        return TestResult(passed=test_result.passed, metric=test_result.metric)


@test(name="Numerical Invariance test", tags=["custom"])
def test_metamorphic_invariance_with_mad(model: BaseModel, dataset: Dataset, column_name: str, value_added: float):
    """
    Metamorphic test for numerical invariance with mean absolute deviation.

    Checks if adding a value to a numerical feature keeps the prediction
    approximately the same using mean absolute deviation.

    Args:
        model: Model to test
        dataset: Dataset to test
        column_name: Name of numerical feature column
        value_added: Value to add to column

    Returns:
        TestResult: Test result with pass/fail
    """
    return test_metamorphic_invariance(
        model=model,
        dataset=dataset,
        transformation_function=mad_transformation(column_name=column_name, value_added=value_added),
    ).execute()
