"""Statistical tests"""
import numbers
import numpy as np
import inspect
from typing import Optional

from giskard import test
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.test_result import TestResult, TestMessage, TestMessageLevel
from giskard.ml_worker.testing.utils import validate_classification_label
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.models.base import BaseModel
from giskard.ml_worker.testing.utils import check_slice_not_empty
from . import debug_prefix


@test(name="Right Label", tags=["heuristic", "classification"])
@validate_classification_label
def test_right_label(
        model: BaseModel,
        dataset: Dataset,
        classification_label: str,
        slicing_function: Optional[SlicingFunction] = None,
        threshold: float = 0.5,
        debug: bool = False
) -> TestResult:
    """
    Summary: Test if the model returns the right classification label for a slice

    Description: The test is passed when the percentage of rows returning the right
    classification label is higher than the threshold in a given slice

    Example: For a credit scoring model, the test is passed when more than 50%
    of people with high-salaries are classified as “non default”


    Args:
      model(BaseModel):
          Model used to compute the test
      dataset(Dataset):
          Dataset used to compute the test
      classification_label(str):
          Classification label you want to test
      slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on the dataset
      threshold(float):
          Threshold for the percentage of passed rows
      debug(bool):
          If True and the test fails,
          a dataset will be provided containing the rows that do not return the right classification label.

    Returns:
      actual_slices_size:
          Length of dataset tested
      metrics:
          The ratio of rows with the right classification label over the total of rows in the slice
      passed:
          TRUE if passed_ratio > threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_right_label")

    prediction_results = model.predict(dataset).prediction

    passed_idx = dataset.df.loc[prediction_results == classification_label].index.values

    passed_ratio = len(passed_idx) / len(dataset)
    passed = bool(passed_ratio > threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.copy()  # copy all properties
        output_ds.df = dataset.df.loc[~dataset.df.index.isin(passed_idx)]
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(
        actual_slices_size=[len(dataset)],
        metric=passed_ratio,
        passed=passed,
        output_df=output_ds
    )


@test(name="Output in range", tags=["heuristic", "classification", "regression"])
@validate_classification_label
def test_output_in_range(
        model: BaseModel,
        dataset: Dataset,
        slicing_function: Optional[SlicingFunction] = None,
        classification_label: Optional[str] = None,
        min_range: float = 0.3,
        max_range: float = 0.7,
        threshold: float = 0.5,
        debug: bool = False
) -> TestResult:
    """
    Summary: Test if the model output belongs to the right range for a slice

    Description: - The test is passed when the ratio of rows in the right range inside the
    slice is higher than the threshold.

    For classification: Test if the predicted probability for a given classification label
    belongs to the right range for a dataset slice

    For regression : Test if the predicted output belongs to the right range for a dataset slice

    Example :
    For Classification: For a credit scoring model, the test is passed when more than 50% of
    people with high wage have a probability of defaulting between 0 and 0.1

    For Regression : The predicted Sale Price of a house in the city falls in a particular range


    Args:
        model(BaseModel):
            Model used to compute the test
        dataset(Dataset):
            Dataset used to compute the test
        slicing_function(Optional[SlicingFunction]):
            Slicing function to be applied on the dataset
        classification_label(Optional[str]):
            Optional. Classification label you want to test
        min_range(float):
            Minimum probability of occurrence of classification label
        max_range(float):
            Maximum probability of occurrence of classification label
        threshold(float):
            Threshold for the percentage of passed rows
        debug(bool):
            If True and the test fails,
            a dataset will be provided containing the rows that are out of the given range.

    Returns:
        actual_slices_size:
            Length of dataset tested
        metrics:
            The proportion of rows in the right range inside the slice
        passed:
            TRUE if metric > threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_output_in_range")

    prediction_results = model.predict(dataset)

    if model.is_regression:
        output = prediction_results.raw_prediction

    elif model.is_classification:
        output = prediction_results.all_predictions[classification_label]

    else:
        raise ValueError(f"Prediction task is not supported: {model.meta.model_type}")

    passed_idx = dataset.df.loc[(output <= max_range) & (output >= min_range)].index.values

    passed_ratio = len(passed_idx) / len(dataset)
    passed = bool(passed_ratio >= threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.copy()  # copy all properties
        output_ds.df = dataset.df.loc[~dataset.df.index.isin(passed_idx)]
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(
        actual_slices_size=[len(dataset)],
        metric=passed_ratio,
        passed=passed,
        output_df=output_ds
    )


@test(name="Disparate impact", tags=["heuristic", "classification"])
def test_disparate_impact(
        model: BaseModel,
        dataset: Dataset,
        protected_slicing_function: SlicingFunction,
        unprotected_slicing_function: SlicingFunction,
        positive_outcome: str,
        slicing_function: Optional[SlicingFunction] = None,
        min_threshold: float = 0.8,
        max_threshold: float = 1.25,
        debug: bool = False,
) -> TestResult:
    """
    Summary: Tests if the model is biased more towards an unprotected slice of the dataset over a protected slice.
    Note that this test reflects only a possible bias in the model while being agnostic to any biaas in the dataset
    it trained on. The Disparate Impact (DI) is only valid for classification models and is computed as the ratio
    between the average count of correct predictions for the protected slice over the unprotected one given a
    certain positive_outcome.

    Description: Calculate the Disparate Impact between a protected and unprotected slice of a dataset. Otherwise
    known as the "80 percent" rule, the Disparate Impact determines if a model was having an "adverse impact" on a
    protected (or minority in some cases) group.

    Example: The rule was originally based on the rates at which job applicants were hired. For example, if XYZ
    Company hired 50 percent of the men applying for work in a predominantly male occupation while hiring only 20
    percent of the female applicants, one could look at the ratio of those two hiring rates to judge whether there
    might be a discrimination problem. The ratio of 20:50 means that the rate of hiring for female applicants is
    only 40 percent of the rate of hiring for male applicants. That is, 20 divided by 50 equals
    0.40, which is equivalent to 40 percent. Clearly, 40 percent is well below the 80 percent that was arbitrarily
    set as an acceptable difference in hiring rates. Therefore, in this example, XYZ Company could have been called
    upon to prove that there was a legitimate reason for hiring men at a rate so much higher than the rate of hiring
    women.

    Args:
          model(BaseModel):
              Model used to compute the test
          dataset(Dataset):
              Dataset used to compute the test
          protected_slicing_function(SlicingFunction):
              Slicing function that defines the protected group from the full dataset given
          unprotected_slicing_function(SlicingFunction):
              Slicing function that defines the unprotected group from the full dataset given
          positive_outcome(str):
              The target value that is considered a positive outcome in the dataset
          slicing_function(Optional[SlicingFunction]):
              Slicing function to be applied on the dataset
          min_threshold(float):
              Threshold below which the DI test is considered to fail, by default 0.8
          max_threshold(float):
              Threshold above which the DI test is considered to fail, by default 1.25
          debug(bool):
              If True and the test fails,
              a dataset will be provided containing the rows from the protected and unprotected slices that were
              incorrectly predicted on a specific positive outcome.

    Returns:
          metric:
              The disparate impact ratio
          passed:
              TRUE if the disparate impact ratio > min_threshold && disparate impact ratio < max_threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_disparate_impact")

    # Try to automatically cast `positive_outcome` to the right type
    if isinstance(model.meta.classification_labels[0], numbers.Number):
        try:
            positive_outcome = float(positive_outcome)
        except ValueError:
            pass

    if positive_outcome not in list(model.meta.classification_labels):
        raise ValueError(
            f"The positive outcome chosen {positive_outcome} is not part of the dataset target values {list(model.meta.classification_labels)}."
        )

    protected_ds = dataset.slice(protected_slicing_function)
    unprotected_ds = dataset.slice(unprotected_slicing_function)

    if protected_ds.df.equals(unprotected_ds.df):
        raise ValueError(
            "The protected and unprotected datasets are equal. Please check that you chose different slices."
        )

    _protected_predictions = model.predict(protected_ds).prediction
    _unprotected_predictions = model.predict(unprotected_ds).prediction

    protected_predictions = np.squeeze(_protected_predictions == positive_outcome)
    unprotected_predictions = np.squeeze(_unprotected_predictions == positive_outcome)

    protected_proba = np.count_nonzero(protected_predictions) / len(protected_ds.df)
    unprotected_proba = np.count_nonzero(unprotected_predictions) / len(unprotected_ds.df)
    disparate_impact_score = protected_proba / unprotected_proba

    messages = [
        TestMessage(
            type=TestMessageLevel.INFO, text=f"min_threshold = {min_threshold}, max_threshold = {max_threshold}"
        )
    ]

    passed = bool((disparate_impact_score > min_threshold) * (disparate_impact_score < max_threshold))

    # --- debug ---
    output_ds = None
    if not passed and debug:
        failed_protected = list(_protected_predictions != protected_ds.df[dataset.target])
        failed_unprotected = list(_unprotected_predictions != unprotected_ds.df[dataset.target])
        failed_idx_protected = [i for i, x in enumerate(failed_protected) if x]
        failed_idx_unprotected = [i for i, x in enumerate(failed_unprotected) if x]
        failed_idx = failed_idx_protected + failed_idx_unprotected
        output_ds = dataset.copy()  # copy all properties
        output_ds.df = dataset.df.iloc[failed_idx]
        test_name = inspect.stack()[1][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(
        metric=disparate_impact_score,
        passed=passed,
        messages=messages,
        output_df=output_ds
    )
