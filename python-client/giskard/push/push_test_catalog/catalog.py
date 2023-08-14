from giskard import SlicingFunction, test
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.utils import Direction, check_slice_not_empty
from giskard.models.base import BaseModel
from typing import Optional

from giskard.testing.tests.performance import _test_diff_prediction, test_rmse, test_f1


@test(name="Slicing RMSE difference", tags=["performance", "regression", "ground_truth", "push"])
def test_diff_rmse_push(
    model: BaseModel,
    reference_dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.1,
    direction: Direction = Direction.Invariant,
    debug: bool = False,
):
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


@test(name="Slicing f1 difference", tags=["performance", "classification", "ground_truth", "push"])
def test_diff_f1_push(
    model: BaseModel,
    reference_dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.1,
    direction: Direction = Direction.Invariant,
    debug: bool = False,
):
    if slicing_function:
        test_name = "test_diff_f1_push"
        actual_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_f1.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="f1",
        debug=debug,
    )
