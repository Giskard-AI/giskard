"""Performance tests"""
import inspect
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from giskard import test
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.test_result import TestResult
from giskard.testing.tests.debug_slicing_functions import incorrect_rows_slicing_fn, \
    nlargest_abs_err_rows_slicing_fn
from giskard.ml_worker.testing.utils import Direction
from giskard.ml_worker.testing.utils import check_slice_not_empty
from giskard.models.base import BaseModel
from giskard.models.utils import np_type_to_native
from . import debug_prefix


def _verify_target_availability(dataset):
    if not dataset.target:
        raise ValueError(
            "This test requires 'target' in Dataset not to be None. 'target' is the column name in df "
            "corresponding to the actual target variable (ground truth). "
            "You can set it when creating your giskard dataset."
        )


def _get_mse(y_actual, y_predicted):
    return mean_squared_error(y_actual, y_predicted)


def _get_rmse(y_actual, y_predicted):
    return np.sqrt(mean_squared_error(y_actual, y_predicted))


def _test_classification_score(score_fn, model: BaseModel, dataset: Dataset, threshold: float = 1.0,
                               debug: bool = False):
    _verify_target_availability(dataset)
    is_binary_classification = len(model.meta.classification_labels) == 2
    targets = dataset.df[dataset.target]
    prediction = model.predict(dataset).prediction
    if is_binary_classification:
        metric = score_fn(targets, prediction, pos_label=model.meta.classification_labels[1])
    else:
        metric = score_fn(targets, prediction, average="micro")

    passed = bool(metric >= threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.slice(incorrect_rows_slicing_fn(dataset.target, prediction=prediction))
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(actual_slices_size=[len(dataset)], metric=metric, passed=passed,
                      output_df=output_ds)


def _test_accuracy_score(dataset: Dataset, model: BaseModel, threshold: float = 1.0, debug: bool = False):
    _verify_target_availability(dataset)
    prediction = model.predict(dataset).prediction
    targets = dataset.df[dataset.target]

    metric = accuracy_score(targets, prediction)
    passed = bool(metric >= threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.slice(incorrect_rows_slicing_fn(dataset.target, prediction=prediction))
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(actual_slices_size=[len(dataset)], metric=metric, passed=passed,
                      output_df=output_ds)


def _test_regression_score(score_fn, model: BaseModel, dataset: Dataset, threshold: float = 1.0, r2=False,
                           debug_percent_rows: float = 0.3, debug: bool = False):
    _verify_target_availability(dataset)

    targets = dataset.df[dataset.target]
    raw_prediction = model.predict(dataset).raw_prediction

    metric = score_fn(targets, raw_prediction)

    passed = bool(metric >= threshold if r2 else metric <= threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.slice(
            nlargest_abs_err_rows_slicing_fn(target=dataset.target, prediction=raw_prediction,
                                             debug_percent_rows=debug_percent_rows))
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(
        actual_slices_size=[len(dataset)],
        metric=metric,
        passed=passed,
        output_df=output_ds
    )


def _test_diff_prediction(
        test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold: float = 0.5,
        direction: Direction = Direction.Invariant,
        test_name=None,
        debug: bool = False
):
    result_reference = test_fn(dataset=reference_dataset, model=model, debug=debug)
    result_actual = test_fn(dataset=actual_dataset, model=model, debug=debug)

    try:
        rel_change = (result_actual.metric - result_reference.metric) / result_reference.metric
    except ZeroDivisionError:
        raise ZeroDivisionError(
            f"Unable to calculate performance difference: the {test_name} inside the"
            " reference_dataset is equal to zero"
        )

    if direction == Direction.Invariant:
        passed = abs(rel_change) < threshold
    elif direction == Direction.Decreasing:
        passed = rel_change < threshold
    elif direction == Direction.Increasing:
        passed = rel_change > threshold
    else:
        raise ValueError(f"Invalid direction: {direction}")

    # --- debug ---
    output_ds = None
    if not passed and debug:
        if result_reference.output_df is None:
            output_ds = result_actual.output_df.copy()
        elif result_actual.output_df is None:
            output_ds = result_reference.output_df.copy()
        else:
            output_ds = result_reference.output_df.copy()  # copy all properties
            output_ds.df = pd.concat([result_actual.output_df.df,
                                      result_reference.output_df.df], ignore_index=True)
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(
        actual_slices_size=[len(actual_dataset)],
        reference_slices_size=[len(reference_dataset)],
        metric=rel_change,
        passed=np_type_to_native(passed),
        output_df=output_ds
    )


@test(name="AUC", tags=["performance", "classification", "ground_truth"])
def test_auc(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0,
        debug: bool = False):
    """
    Test if the model AUC performance is higher than a threshold for a given slice

    Example : The test is passed when the AUC for females is higher than 0.7


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Actual dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value of AUC metrics
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows.

    Returns:
      actual_slices_size:
          Length of dataset tested
      metric:
          The AUC performance metric
      passed:
          TRUE if AUC metrics >= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_auc")

    _predictions = model.predict(dataset)
    targets = dataset.df[dataset.target]

    _verify_target_availability(dataset)
    if len(model.meta.classification_labels) == 2:
        metric = roc_auc_score(targets, model.predict(dataset).raw[:, 1])
    else:
        predictions = _predictions.all_predictions
        non_declared_categories = set(predictions.columns) - set(targets.unique())
        assert not len(non_declared_categories), (
            f'Predicted classes don\'t exist in the dataset "{dataset.target}" column: {non_declared_categories}. '
            "ROC AUC score is not defined in that case."
        )

        metric = roc_auc_score(targets, predictions, multi_class="ovo")

    passed = bool(metric >= threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.slice(incorrect_rows_slicing_fn(dataset.target, prediction=_predictions.prediction))
        test_name = inspect.stack()[0][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(actual_slices_size=[len(dataset)], metric=metric, passed=passed,
                      output_df=output_ds)


@test(name="F1", tags=["performance", "classification", "ground_truth"])
def test_f1(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0
        ,
        debug: bool = False):
    """
    Test if the model F1 score is higher than a defined threshold for a given slice

    Example: The test is passed when F1 score for females is higher than 0.7


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Actual dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for F1 Score
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows.

    Returns:
        actual_slices_size:
          Length of dataset tested
        metric:
          The F1 score metric
        passed:
          TRUE if F1 Score metrics >= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_f1")
    return _test_classification_score(f1_score, model, dataset, threshold, debug)


@test(name="Accuracy", tags=["performance", "classification", "ground_truth"])
def test_accuracy(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0
        ,
        debug: bool = False):
    """
    Test if the model Accuracy is higher than a threshold for a given slice

    Example: The test is passed when the Accuracy for females is higher than 0.7


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Actual dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for Accuracy
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows.

    Returns:
      actual_slices_size:
          Length of dataset tested
      metric:
          The Accuracy metric
      passed:
          TRUE if Accuracy metrics >= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_accuracy")
    return _test_accuracy_score(dataset, model, threshold, debug)


@test(name="Precision", tags=["performance", "classification", "ground_truth"])
def test_precision(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0,
        debug: bool = False
):
    """
    Test if the model Precision is higher than a threshold for a given slice

    Example: The test is passed when the Precision for females is higher than 0.7


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Actual dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for Precision
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows.

    Returns:
        actual_slices_size:
          Length of dataset tested
        metric:
          The Precision metric
        passed:
          TRUE if Precision metrics >= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_precision")
    return _test_classification_score(precision_score, model, dataset, threshold, debug)


@test(name="Recall", tags=["performance", "classification", "ground_truth"])
def test_recall(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0,
        debug: bool = False):
    """
    Test if the model Recall is higher than a threshold for a given slice

    Example: The test is passed when the Recall for females is higher than 0.7


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Actual dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for Recall
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows.

    Returns:
        actual_slices_size:
          Length of dataset tested
        metric:
          The Recall metric
        passed:
          TRUE if Recall metric >= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_recall")
    return _test_classification_score(recall_score, model, dataset, threshold, debug)


@test(name="RMSE", tags=["performance", "regression", "ground_truth"])
def test_rmse(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0
        ,
        debug_percent_rows: float = 0.3, debug: bool = False):
    """
    Test if the model RMSE is lower than a threshold

    Example: The test is passed when the RMSE is lower than 10


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for RMSE
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing the top debug_percent_rows
          of the rows with the highest absolute error (difference between prediction and data).

    Returns:
        actual_slices_size:
          Length of dataset tested
        metric:
          The RMSE metric
        passed:
          TRUE if RMSE metric <= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_rmse")
    return _test_regression_score(_get_rmse, model, dataset, threshold, debug_percent_rows=debug_percent_rows,
                                  debug=debug)


@test(name="MSE", tags=["performance", "regression", "ground_truth"])
def test_mse(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0,
        debug_percent_rows: float = 0.3, debug: bool = False
):
    """
    Test if the model mean squared error (MSE) is lower than a threshold.

    Example: The test is passed when the MSE is lower than 10.


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for MSE
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing the top debug_percent_rows
          of the rows with the highest absolute error (difference between prediction and data).

    Returns:
        actual_slices_size:
          Length of dataset tested
        metric:
          The MSE metric
        passed:
          True if MSE metric <= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_mse")
    return _test_regression_score(_get_mse, model, dataset, threshold, debug_percent_rows=debug_percent_rows,
                                  debug=debug)


@test(name="MAE", tags=["performance", "regression", "ground_truth"])
def test_mae(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0
        ,
        debug_percent_rows: float = 0.3, debug: bool = False):
    """
    Test if the model Mean Absolute Error is lower than a threshold

    Example: The test is passed when the MAE is lower than 10


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for MAE
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing the top debug_percent_rows
          of the rows with the highest absolute error (difference between prediction and data).

    Returns:
        actual_slices_size:
          Length of dataset tested
        reference_slices_size:
          Length of reference_dataset tested
        metric:
          The MAE metric
        passed:
          TRUE if MAE metric <= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_mae")
    return _test_regression_score(mean_absolute_error, model, dataset, threshold, debug_percent_rows=debug_percent_rows,
                                  debug=debug)


@test(name="R2", tags=["performance", "regression", "ground_truth"])
def test_r2(
        model: BaseModel, dataset: Dataset, slicing_function: Optional[SlicingFunction] = None, threshold: float = 1.0
        ,
        debug_percent_rows: float = 0.3, debug: bool = False):
    """
    Test if the model R-Squared is higher than a threshold

    Example: The test is passed when the R-Squared is higher than 0.7


    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold value for R-Squared
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing the top debug_percent_rows
          of the rows with the highest absolute error (difference between prediction and data).

    Returns:
        actual_slices_size:
          Length of dataset tested
        metric:
          The R-Squared metric
        passed:
          TRUE if R-Squared metric >= threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_r2")
    return _test_regression_score(r2_score, model, dataset, threshold, r2=True, debug_percent_rows=debug_percent_rows,
                                  debug=debug)


@test(name="Accuracy difference", tags=["performance", "classification", "ground_truth"])
def test_diff_accuracy(
        model: BaseModel,
        actual_dataset: Dataset,
        reference_dataset: Dataset,
        slicing_function: Optional[SlicingFunction] = None,
        threshold: float = 0.1,
        direction: Direction = Direction.Invariant,
        debug: bool = False
):
    """

    Test if the absolute percentage change of model Accuracy between two samples is lower than a threshold

    Example : The test is passed when the Accuracy for females has a difference lower than 10% from the
    Accuracy for males. For example, if the Accuracy for males is 0.8 (dataset) and the Accuracy  for
    females is 0.6 (reference_dataset) then the absolute percentage Accuracy change is 0.2 / 0.8 = 0.25
    and the test will fail


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
          Threshold value for Accuracy Score difference
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows from both actual_dataset and
          reference_dataset
    Returns:
        actual_slices_size:
          Length of dataset tested
        reference_slices_size:
          Length of reference_dataset tested
        metric:
          The Accuracy difference  metric
        passed:
          TRUE if Accuracy difference < threshold
    """
    if slicing_function:
        test_name = "test_diff_accuracy"
        actual_dataset = actual_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        reference_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_accuracy.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="Accuracy",
        debug=debug
    )


@test(name="F1 difference", tags=["performance", "classification", "ground_truth"])
def test_diff_f1(
        model: BaseModel,
        actual_dataset: Dataset,
        reference_dataset: Dataset,
        slicing_function: Optional[SlicingFunction] = None,
        threshold: float = 0.1,
        direction: Direction = Direction.Invariant,
        debug: bool = False
):
    """
    Test if the absolute percentage change in model F1 Score between two samples is lower than a threshold

    Example : The test is passed when the F1 Score for females has a difference lower than 10% from the
    F1 Score for males. For example, if the F1 Score for males is 0.8 (dataset) and the F1 Score  for
    females is 0.6 (reference_dataset) then the absolute percentage F1 Score  change is 0.2 / 0.8 = 0.25
    and the test will fail


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
          Threshold value for F1 Score difference
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows from both actual_dataset and
          reference_dataset
    Returns:
        actual_slices_size:
          Length of dataset tested
        reference_slices_size:
          Length of reference_dataset tested
        metric:
          The F1 Score difference  metric
        passed:
          TRUE if F1 Score difference < threshold
    """
    if slicing_function:
        test_name = "test_diff_f1"
        actual_dataset = actual_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        reference_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_f1.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="F1 Score",
        debug=debug
    )


@test(name="Precision difference", tags=["performance", "classification", "ground_truth"])
def test_diff_precision(
        model: BaseModel,
        actual_dataset: Dataset,
        reference_dataset: Dataset,
        slicing_function: Optional[SlicingFunction] = None,
        threshold: float = 0.1,
        direction: Direction = Direction.Invariant,
        debug: bool = False
):
    """
    Test if the absolute percentage change of model Precision between two samples is lower than a threshold

    Example : The test is passed when the Precision for females has a difference lower than 10% from the
    Accuracy for males. For example, if the Precision for males is 0.8 (dataset) and the Precision  for
    females is 0.6 (reference_dataset) then the absolute percentage Precision change is 0.2 / 0.8 = 0.25
    and the test will fail


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
          Threshold value for Precision difference
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows from both actual_dataset and
          reference_dataset
    Returns:
        actual_slices_size:
          Length of dataset tested
        reference_slices_size:
          Length of reference_dataset tested
        metric:
          The Precision difference  metric
        passed:
          TRUE if Precision difference < threshold
    """
    if slicing_function:
        test_name = "test_diff_precision"
        actual_dataset = actual_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        reference_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_precision.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="Precision",
        debug=debug
    )


@test(name="Recall difference", tags=["performance", "classification", "ground_truth"])
def test_diff_recall(
        model: BaseModel,
        actual_dataset: Dataset,
        reference_dataset: Dataset,
        slicing_function: Optional[SlicingFunction] = None,
        threshold: float = 0.1,
        direction: Direction = Direction.Invariant,
        debug: bool = False
):
    """
    Test if the absolute percentage change of model Recall between two samples is lower than a threshold

    Example : The test is passed when the Recall for females has a difference lower than 10% from the
    Accuracy for males. For example, if the Recall for males is 0.8 (dataset) and the Recall  for
    females is 0.6 (reference_dataset) then the absolute percentage Recall change is 0.2 / 0.8 = 0.25
    and the test will fail


    Args:
        model(BaseModel):
          Model used to compute the test
        actual_dataset(Dataset):
          Actual dataset used to compute the test
        reference_dataset(Dataset):
          Actual dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on both actual and reference datasets
        threshold(float):
          Threshold value for Recall difference
        debug(bool):
          If True and the test fails,
          a dataset will be provided containing all the incorrectly predicted rows from both actual_dataset and
          reference_dataset
    Returns:
        actual_slices_size:
          Length of dataset tested
        reference_slices_size:
          Length of reference_dataset tested
        metric:
          The Recall difference  metric
        passed:
          TRUE if Recall difference < threshold
    """
    if slicing_function:
        test_name = "test_diff_recall"
        actual_dataset = actual_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        reference_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_recall.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="Recall",
        debug=debug
    )


@test(name="RMSE difference", tags=["performance", "regression", "ground_truth"])
def test_diff_rmse(
        model: BaseModel,
        actual_dataset: Dataset,
        reference_dataset: Dataset,
        slicing_function: Optional[SlicingFunction] = None,
        threshold: float = 0.1,
        direction: Direction = Direction.Invariant,
        debug: bool = False
):
    """
    Test if the absolute percentage change of model RMSE between two samples is lower than a threshold

    Example : The test is passed when the RMSE for females has a difference lower than 10% from the
    RMSE for males. For example, if the RMSE for males is 0.8 (dataset) and the RMSE  for
    females is 0.6 (reference_dataset) then the absolute percentage RMSE change is 0.2 / 0.8 = 0.25
    and the test will fail


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
        test_name = "test_diff_rmse"
        actual_dataset = actual_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=actual_dataset, dataset_name="actual_dataset", test_name=test_name)
        reference_dataset = reference_dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=reference_dataset, dataset_name="reference_dataset", test_name=test_name)

    return _test_diff_prediction(
        test_rmse.test_fn,
        model,
        actual_dataset,
        reference_dataset,
        threshold=threshold,
        direction=direction,
        test_name="RMSE",
        debug=debug
    )
