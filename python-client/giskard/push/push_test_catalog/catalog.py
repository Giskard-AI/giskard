from giskard import SlicingFunction, test
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.utils import Direction, check_slice_not_empty
from giskard.models.base import BaseModel
from typing import Optional

from giskard.testing.tests.performance import _test_diff_prediction, test_rmse


@test(name="Slicing RMSE difference", tags=["performance", "regression", "ground_truth", "push"])
def test_diff_rmse_push(
    model: BaseModel,
    reference_dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.1,
    direction: Direction = Direction.Invariant,
    debug: bool = False,
):
    """
    Test if the absolute percentage change of model RMSE between the detected slice and the whole dataset is lower than a threshold

    Args:
        model(BaseModel):
          Model used to compute the test
        actual_dataset(Dataset):
          Actual dataset used to compute the test
        reference_dataset(Dataset):
          Reference dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on both actual and reference datasets
        threshold(float):
          Threshold value for RMSE difference
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing the top debug_percent_rows
          of the rows with the highest absolute error (difference between prediction and data) from both
          actual_dataset and reference_dataset.

    Returns:
        actual_slices_size:
          Length of dataset tested
        reference_slices_size:
          Length of reference_dataset tested
        metric:
          The RMSE difference  metric
        passed:
          TRUE if RMSE difference < threshold
    """
    if slicing_function:
        test_name = "test_diff_rmse_push"
        actual_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_rmse.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="RMSE",
        debug=debug,
    )


# def test_diff_f1_push(
#     model: BaseModel,
#     reference_dataset: Dataset,
#     slicing_function: Optional[SlicingFunction] = None,
#     threshold: float = 0.1,
#     direction: Direction = Direction.Invariant,
#     debug: bool = False,
# ):
