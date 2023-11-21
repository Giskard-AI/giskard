from typing import Optional

import numpy as np
import pandas as pd

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.llm import LLMImportError
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
from giskard.ml_worker.testing.stat_utils import (
    equivalence_t_test,
    equivalence_wilcoxon,
    paired_t_test,
    paired_wilcoxon,
)
from giskard.ml_worker.testing.test_result import TestMessage, TestMessageLevel, TestResult
from giskard.ml_worker.testing.utils import Direction, check_slice_not_empty, validate_classification_label
from giskard.ml_worker.utils.logging import timer
from giskard.models.base import BaseModel
from giskard.models.utils import fix_seed
from . import debug_description_prefix


def _predict_numeric_result(model: BaseModel, ds: Dataset, output_proba=True, classification_label=None):
    if model.is_text_generation:
        return model.predict(ds).raw_prediction.flatten()
    if model.is_regression or not output_proba:
        return model.predict(ds).raw_prediction
    elif model.is_classification and classification_label is not None:
        return model.predict(ds).all_predictions[classification_label].values
    elif model.is_classification:
        return model.predict(ds).probabilities


def _prediction_ratio(prediction, perturbed_prediction):
    return abs(perturbed_prediction - prediction) / prediction if prediction != 0 else abs(perturbed_prediction)


@timer("Perturb and predict data")
def _perturb_and_predict(
    model: BaseModel,
    ds: Dataset,
    transformation_function: TransformationFunction,
    output_proba=True,
    classification_label=None,
):
    fix_seed()

    results_df = pd.DataFrame(
        {
            "prediction": _predict_numeric_result(model, ds, output_proba, classification_label),
        },
        index=ds.df.index,
    )

    perturbed_ds = ds.transform(transformation_function)
    results_df["perturbed_prediction"] = _predict_numeric_result(
        model, perturbed_ds, output_proba, classification_label
    )
    modified_idx = ds.df.compare(perturbed_ds.df).index

    return results_df.loc[modified_idx], len(modified_idx)


@timer("Compare and predict the data")
def _compare_prediction(results_df, prediction_task, direction, output_sensitivity=None):
    if direction == Direction.Invariant:
        if prediction_task == SupportedModelTypes.CLASSIFICATION:
            passed_idx = results_df.loc[results_df["prediction"] == results_df["perturbed_prediction"]].index.values

        elif prediction_task == SupportedModelTypes.TEXT_GENERATION:
            try:
                import evaluate

                scorer = evaluate.load("bertscore")
            except ImportError as err:
                raise LLMImportError() from err
            except FileNotFoundError as err:
                raise LLMImportError(
                    "Your version of evaluate does not support 'bertscore'. "
                    "Please use 'pip install -U evaluate' to upgrade it"
                ) from err

            score = scorer.compute(
                predictions=results_df["perturbed_prediction"].values,
                references=results_df["prediction"].values,
                model_type="distilbert-base-multilingual-cased",
                idf=True,
            )
            passed = np.array(score["f1"]) > 1 - output_sensitivity
            passed_idx = results_df.loc[passed].index.values

        elif prediction_task == SupportedModelTypes.REGRESSION:
            results_df["predict_difference_ratio"] = results_df.apply(
                lambda x: _prediction_ratio(x["prediction"], x["perturbed_prediction"]),
                axis=1,
            )
            output_sensitivity = 0.1 if not output_sensitivity else output_sensitivity
            passed_idx = results_df.loc[results_df["predict_difference_ratio"] < output_sensitivity].index.values
        else:
            raise ValueError(f"Invalid prediction task: {prediction_task}")

    elif direction == Direction.Increasing:
        passed_idx = results_df.loc[results_df["prediction"] < results_df["perturbed_prediction"]].index.values

    elif direction == Direction.Decreasing:
        passed_idx = results_df.loc[results_df["prediction"] > results_df["perturbed_prediction"]].index.values
    else:
        raise ValueError(f"Invalid direction: {direction}")

    failed_idx = results_df.loc[~results_df.index.isin(passed_idx)].index.values
    return passed_idx, failed_idx


def _compare_probabilities_t_test(result_df, direction, window_size=0.1, critical_quantile=0.05):
    if direction == Direction.Invariant:
        p_value = equivalence_t_test(
            result_df["prediction"],
            result_df["perturbed_prediction"],
            window_size=window_size,
            critical_quantile=critical_quantile,
        )[1]

    elif direction == Direction.Increasing:
        p_value = paired_t_test(
            result_df["prediction"],
            result_df["perturbed_prediction"],
            alternative="less",
            critical_quantile=critical_quantile,
        )[1]

    elif direction == Direction.Decreasing:
        p_value = paired_t_test(
            result_df["prediction"],
            result_df["perturbed_prediction"],
            alternative="greater",
            critical_quantile=critical_quantile,
        )[1]

    return p_value


def _compare_probabilities_wilcoxon(result_df, direction, window_size=0.2, critical_quantile=0.05):
    if direction == Direction.Invariant:
        p_value = equivalence_wilcoxon(
            result_df["prediction"],
            result_df["perturbed_prediction"],
            window_size=window_size,
            critical_quantile=critical_quantile,
        )[1]

    elif direction == Direction.Increasing:
        p_value = paired_wilcoxon(
            result_df["prediction"],
            result_df["perturbed_prediction"],
            alternative="less",
            critical_quantile=critical_quantile,
        )[1]

    elif direction == Direction.Decreasing:
        p_value = paired_wilcoxon(
            result_df["prediction"],
            result_df["perturbed_prediction"],
            alternative="greater",
            critical_quantile=critical_quantile,
        )[1]

    return p_value


def _test_metamorphic(
    model,
    direction: Direction,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    threshold: float,
    classification_label=None,
    output_sensitivity=None,
    output_proba=True,
    debug: bool = False,  # noqa: NOSONAR - old version tests will call this under legacy debug mode
) -> TestResult:
    results_df, modified_rows_count = _perturb_and_predict(
        model, dataset, transformation_function, output_proba=output_proba, classification_label=classification_label
    )

    passed_idx, failed_idx = _compare_prediction(results_df, model.meta.model_type, direction, output_sensitivity)
    passed_ratio = len(passed_idx) / modified_rows_count if modified_rows_count != 0 else 1

    messages = [TestMessage(type=TestMessageLevel.INFO, text=f"{modified_rows_count} rows were perturbed")]

    passed = bool(passed_ratio > threshold)
    # --- debug ---
    output_ds = list()
    if not passed:
        output_ds.append(dataset.slice(lambda df: df.loc[failed_idx], row_level=False))
    # ---

    return TestResult(
        actual_slices_size=[len(dataset.df)],
        metric=passed_ratio,
        passed=passed,
        messages=messages,
        output_ds=output_ds,
    )


@test(
    name="Invariance (proportion)",
    debug_description=debug_description_prefix + "that are <b>non-invariant after perturbation</b>.",
)
def test_metamorphic_invariance(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.5,
    output_sensitivity: float = None,
):
    """
    Summary: Tests if the model prediction is invariant when the feature values are perturbed

    Description: -
    For classification: Test if the predicted classification label remains the same after
    feature values perturbation.
    For regression: Check whether the predicted output remains the same at the output_sensibility
    level after feature values perturbation.

    The test is passed when the ratio of invariant rows is higher than the threshold

    Example : The test is passed when, after switching gender from male to female,
    more than 50%(threshold 0.5) of males have unchanged outputs

    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        transformation_function(TransformationFunction):
          Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        output_sensitivity(float):
            Optional. The threshold for ratio between the difference between perturbed prediction and actual prediction over
            the actual prediction for a regression model. We consider there is a prediction difference for
            regression if the ratio is above the output_sensitivity of 0.1

    Returns:
        actual_slices_size:
          Length of dataset tested
        message:
          Test result message
        metric:
          The ratio of unchanged rows over the perturbed rows
        passed:
          TRUE if metric > threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_invariance")

    return _test_metamorphic(
        direction=Direction.Invariant,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        threshold=threshold,
        output_sensitivity=output_sensitivity,
        output_proba=False,
    )


@test(
    name="Increasing (proportion)",
    debug_description=debug_description_prefix + "that are <b>non-increasing after perturbation</b>.",
)
@validate_classification_label
def test_metamorphic_increasing(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.5,
    classification_label: str = None,
):
    """
    Summary: Tests if the model probability increases when the feature values are perturbed

    Description: -
    - For classification: Test if the model probability of a given classification_label is
    increasing after feature values perturbation.

    - For regression: Test if the model prediction is increasing after feature values perturbation.

    The test is passed when the percentage of rows that are increasing is higher than the threshold

    Example : For a credit scoring model, the test is passed when a decrease of wage by 10%,
     default probability is increasing for more than 50% of people in the dataset

    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        transformation_function(TransformationFunction):
          Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        classification_label(str):
          Optional.One specific label value from the target column

    Returns:
        actual_slices_size:
          Length of dataset tested
        message:
          Test result message
        metric:
          The ratio of increasing rows over the perturbed rows
        passed:
          TRUE if metric > threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_increasing")

    return _test_metamorphic(
        direction=Direction.Increasing,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        classification_label=classification_label,
        threshold=threshold,
    )


@test(
    name="Decreasing (proportion)",
    debug_description=debug_description_prefix + "that are <b>non-decreasing after perturbation</b>.",
)
@validate_classification_label
def test_metamorphic_decreasing(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.5,
    classification_label: str = None,
):
    """
    Summary: Tests if the model probability decreases when the feature values are perturbed

    Description: -
    - For classification: Test if the model probability of a given classification_label is
    decreasing after feature values perturbation.

    - For regression: Test if the model prediction is decreasing after feature values perturbation.

    The test is passed when the percentage of rows that are decreasing is higher than the threshold

    Example : For a credit scoring model, the test is passed when an increase of wage by 10%,
     default probability is decreasing for more than 50% of people in the dataset

    Args:
        model(BaseModel):
          Model used to compute the test
        dataset(Dataset):
          Dataset used to compute the test
        transformation_function(TransformationFunction):
          Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        threshold(float):
          Threshold of the ratio of decreasing rows
        classification_label(str):
          Optional. One specific label value from the target column

    Returns:
        actual_slices_size:
          Length of dataset tested
        message:
          Test result message
        metric:
          The ratio of decreasing rows over the perturbed rows
        passed:
          TRUE if metric > threshold
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_decreasing")

    return _test_metamorphic(
        direction=Direction.Decreasing,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        classification_label=classification_label,
        threshold=threshold,
    )


def _test_metamorphic_t_test(
    direction: Direction,
    model,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    window_size: float,
    critical_quantile: float,
    classification_label=None,
    output_proba=True,
    debug: bool = False,  # noqa: NOSONAR - old version tests will call this under legacy debug mode
) -> TestResult:
    result_df, modified_rows_count = _perturb_and_predict(
        model, dataset, transformation_function, output_proba=output_proba, classification_label=classification_label
    )

    p_value = _compare_probabilities_t_test(result_df, direction, window_size, critical_quantile)

    messages = [TestMessage(type=TestMessageLevel.INFO, text=f"{modified_rows_count} rows were perturbed")]

    return _create_test_result(critical_quantile, dataset, direction, messages, model, p_value, result_df, debug)


def _create_test_result(
    critical_quantile,
    dataset,
    direction,
    messages,
    model,
    p_value,
    result_df,
    debug: bool = False,  # noqa: NOSONAR - old version tests will call this under legacy debug mode
):
    passed = bool(p_value < critical_quantile)
    # --- debug ---
    output_ds = list()
    if not passed:
        _, failed_idx = _compare_prediction(result_df, model.meta.model_type, direction, None)
        output_ds.append(dataset.slice(lambda df: df.loc[failed_idx], row_level=False))
    # ---
    return TestResult(
        actual_slices_size=[len(dataset.df)],
        metric=p_value,
        passed=passed,
        messages=messages,
        output_ds=output_ds,
    )


@test(
    name="Decreasing (t-test)",
    debug_description=debug_description_prefix + "that are <b>non-decreasing after perturbation</b>.",
)
@validate_classification_label
def test_metamorphic_decreasing_t_test(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    critical_quantile: float = 0.05,
    classification_label: str = None,
):
    """
    Summary: Tests if the model probability decreases when the feature values are perturbed

    Description: Calculate the t-test on TWO RELATED samples. Sample (A) is the original probability predictions
    while sample (B) is the probabilities after perturbation of one or more of the features.
    This test computes the decreasing test to study if mean(B) < mean(A)
    The test is passed when the p-value of the t-test between (A) and (B) is below the critical quantile

    Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
             causes a statistically significant probability decrease.

    Args:
        model(BaseModel):
            Model used to compute the test
        dataset(Dataset):
            Dataset used to compute the test
        transformation_function(TransformationFunction):
            Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        critical_quantile(float):
            Critical quantile above which the null hypothesis cannot be rejected

    Returns:
        actual_slices_size:
            Length of dataset tested
        message:
            Test result message
        metric:
            The t-test in terms of p-value between unchanged rows over the perturbed rows
        passed:
            TRUE if the p-value of the t-test between (A) and (B) is below the critical value
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(
            sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_decreasing_t_test"
        )

    return _test_metamorphic_t_test(
        direction=Direction.Decreasing,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        window_size=float("nan"),
        critical_quantile=critical_quantile,
        classification_label=classification_label,
    )


@test(
    name="Increasing (t-test)",
    debug_description=debug_description_prefix + "that are <b>non-increasing after perturbation</b>.",
)
@validate_classification_label
def test_metamorphic_increasing_t_test(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    critical_quantile: float = 0.05,
    classification_label: str = None,
):
    """
    Summary: Tests if the model probability increases when the feature values are perturbed

    Description: Calculate the t-test on TWO RELATED samples. Sample (A) is the original probability predictions
    while sample (B) is the probabilities after perturbation of one or more of the features.
    This test computes the increasing test to study if mean(A) < mean(B)
    The test is passed when the p-value of the t-test between (A) and (B) is below the critical quantile

    Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
             causes a statistically significant probability increase.

    Args:
        model(BaseModel):
            Model used to compute the test
        dataset(Dataset):
            Dataset used to compute the test
        transformation_function(TransformationFunction):
            Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
          Slicing function to be applied on dataset
        critical_quantile(float):
            Critical quantile above which the null hypothesis cannot be rejected

    Returns:
        actual_slices_size:
            Length of dataset tested
        message:
            Test result message
        metric:
            The t-test in terms of p-value between unchanged rows over the perturbed rows
        passed:
            TRUE if the p-value of the t-test between (A) and (B) is below the critical value
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(
            sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_increasing_t_test"
        )

    return _test_metamorphic_t_test(
        direction=Direction.Increasing,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        window_size=float("nan"),
        critical_quantile=critical_quantile,
        classification_label=classification_label,
    )


@test(
    name="Invariance (t-test)",
    debug_description=debug_description_prefix + "that are <b>non-invariant after perturbation</b>.",
)
def test_metamorphic_invariance_t_test(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    window_size: float = 0.2,
    critical_quantile: float = 0.05,
) -> TestResult:
    """
    Summary: Tests if the model predictions are statistically invariant when the feature values are perturbed.

    Description: Calculate the t-test on TWO RELATED samples. Sample (A) is the original probability predictions
    while sample (B) is the probabilities after perturbation of one or more of the features.
    This test computes the equivalence test to show that mean(B) - window_size/2 < mean(A) < mean(B) + window_size/2
    The test is passed when the following tests pass:
      - the p-value of the t-test between (A) and (B)+window_size/2 is below the critical quantile
      - the p-value of the t-test between (B)-window_size/2 and (A) is below the critical quantile

    Example: The test is passed when, after switching gender from male to female,
    the probability distributions remains statistically invariant. In other words, the test is passed if the mean of the
    perturbed sample is statistically within a window determined by the user.

    Args:
          model(BaseModel):
              Model used to compute the test
          dataset(Dataset):
              Dataset used to compute the test
          transformation_function(TransformationFunction):
              Function performing the perturbations to be applied on dataset.
          slicing_function(Optional[SlicingFunction]):
              Slicing function to be applied on dataset
          window_size(float):
              Probability window in which the mean of the perturbed sample can be in
          critical_quantile(float):
              Critical quantile above which the null hypothesis cannot be rejected

    Returns:
          actual_slices_size:
              Length of dataset tested
          message:
              Test result message
          metric:
              The t-test in terms of p-value between unchanged rows over the perturbed rows
          passed:
              TRUE if the p-value of the t-test between (A) and (B)+window_size/2 < critical_quantile && the p-value of the t-test between (B)-window_size/2 and (A) < critical_quantile
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(
            sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_invariance_t_test"
        )

    return _test_metamorphic_t_test(
        direction=Direction.Invariant,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        window_size=window_size,
        critical_quantile=critical_quantile,
        output_proba=False,
    )


def _test_metamorphic_wilcoxon(
    direction: Direction,
    model,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    window_size: float,
    critical_quantile: float,
    classification_label=None,
    output_proba=True,
    debug: bool = False,  # noqa: NOSONAR - old version tests will call this under legacy debug mode
) -> TestResult:
    result_df, modified_rows_count = _perturb_and_predict(
        model, dataset, transformation_function, output_proba=output_proba, classification_label=classification_label
    )

    p_value = _compare_probabilities_wilcoxon(result_df, direction, window_size, critical_quantile)

    messages = [TestMessage(type=TestMessageLevel.INFO, text=f"{modified_rows_count} rows were perturbed")]

    return _create_test_result(critical_quantile, dataset, direction, messages, model, p_value, result_df, debug)


@test(
    name="Decreasing (Wilcoxon)",
    debug_description=debug_description_prefix + "that are <b>non-decreasing after perturbation</b>.",
)
@validate_classification_label
def test_metamorphic_decreasing_wilcoxon(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    critical_quantile: float = 0.05,
    classification_label: str = None,
):
    """
    Summary: Tests if the model probability decreases when the feature values are perturbed

    Description: Calculate the Wilcoxon signed-rank test on TWO RELATED samples. Sample (A) is the original probability predictions
    while sample (B) is the probabilities after perturbation of one or more of the features.
    This test computes the decreasing test to study if mean(B) < mean(A)
    The test is passed when the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical quantile

    Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
             causes a statistically significant probability decrease.

    Args:
        model(BaseModel):
            Model used to compute the test
        dataset(Dataset):
            Dataset used to compute the test
        transformation_function(TransformationFunction):
            Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
            Slicing function to be applied on dataset
        critical_quantile(float):
            Critical quantile above which the null hypothesis cannot be rejected

    Returns:
        actual_slices_size:
            Length of dataset tested
        message:
            Test result message
        metric:
            The Wilcoxon signed-rank test in terms of p-value between unchanged rows over the perturbed rows
        passed:
            TRUE if the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical value
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(
            sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_decreasing_wilcoxon"
        )

    return _test_metamorphic_wilcoxon(
        direction=Direction.Decreasing,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        classification_label=classification_label,
        window_size=float("nan"),
        critical_quantile=critical_quantile,
    )


@test(
    name="Increasing (Wilcoxon)",
    debug_description=debug_description_prefix + "that are <b>non-increasing after perturbation</b>.",
)
@validate_classification_label
def test_metamorphic_increasing_wilcoxon(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    critical_quantile: float = 0.05,
    classification_label: str = None,
):
    """
    Summary: Tests if the model probability increases when the feature values are perturbed

    Description: Calculate the Wilcoxon signed-rank test on TWO RELATED samples. Sample (A) is the original probability predictions
    while sample (B) is the probabilities after perturbation of one or more of the features.
    This test computes the increasing test to study if mean(A) < mean(B)
    The test is passed when the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical quantile

    Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
             causes a statistically significant probability increase.

    Args:
        model(BaseModel):
            Model used to compute the test
        dataset(Dataset):
            Dataset used to compute the test
        transformation_function(TransformationFunction):
            Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
            Slicing function to be applied on dataset
        critical_quantile(float):
            Critical quantile above which the null hypothesis cannot be rejected

    Returns:
        actual_slices_size:
            Length of dataset tested
        message:
            Test result message
        metric:
            The Wilcoxon signed-rank test in terms of p-value between unchanged rows over the perturbed rows
        passed:
            TRUE if the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical value
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(
            sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_increasing_wilcoxon"
        )

    return _test_metamorphic_wilcoxon(
        direction=Direction.Increasing,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        classification_label=classification_label,
        window_size=float("nan"),
        critical_quantile=critical_quantile,
    )


@test(
    name="Invariance (Wilcoxon)",
    debug_description=debug_description_prefix + "that are <b>non-invariant after perturbation</b>.",
)
def test_metamorphic_invariance_wilcoxon(
    model: BaseModel,
    dataset: Dataset,
    transformation_function: TransformationFunction,
    slicing_function: Optional[SlicingFunction] = None,
    window_size: float = 0.2,
    critical_quantile: float = 0.05,
) -> TestResult:
    """
    Summary: Tests if the model predictions are statistically invariant when the feature values are perturbed.

    Description: Calculate the Wilcoxon signed-rank test on TWO RELATED samples. Sample (A) is the original probability predictions
    while sample (B) is the probabilities after perturbation of one or more of the features.
    This test computes the equivalence test to show that mean(B) - window_size/2 < mean(A) < mean(B) + window_size/2
    The test is passed when the following tests pass:
    - the p-value of the t-test between (A) and (B)+window_size/2 is below the critical quantile
    - the p-value of the t-test between (B)-window_size/2 and (A) is below the critical quantile

    Example: The test is passed when, after switching gender from male to female,
    the probability distributions remains statistically invariant. In other words, the test is passed if the mean of the
    perturbed sample is statistically within a window determined by the user.

    Args:
        model(BaseModel):
            Model used to compute the test
        dataset(Dataset):
            Dataset used to compute the test
        transformation_function(TransformationFunction):
            Function performing the perturbations to be applied on dataset.
        slicing_function(Optional[SlicingFunction]):
            Slicing function to be applied on dataset
        window_size(float):
            Probability window in which the mean of the perturbed sample can be in
        critical_quantile(float):
            Critical quantile above which the null hypothesis cannot be rejected

    Returns:
        actual_slices_size:
            Length of dataset tested
        message:
            Test result message
        metric:
            The t-test in terms of p-value between unchanged rows over the perturbed rows
        passed:
            TRUE if the p-value of the Wilcoxon signed-rank test between (A) and (B)+window_size/2 < critical_quantile && the p-value of the t-test between (B)-window_size/2 and (A) < critical_quantile
    """
    if slicing_function:
        dataset = dataset.slice(slicing_function)
        check_slice_not_empty(
            sliced_dataset=dataset, dataset_name="dataset", test_name="test_metamorphic_invariance_wilcoxon"
        )

    return _test_metamorphic_wilcoxon(
        direction=Direction.Invariant,
        dataset=dataset,
        model=model,
        transformation_function=transformation_function,
        window_size=window_size,
        critical_quantile=critical_quantile,
        output_proba=False,
    )
