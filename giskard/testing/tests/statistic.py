"""Statistical tests"""
import numbers
from typing import Optional

import numpy as np

from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.decorators import test
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.test_result import TestMessage, TestMessageLevel, TestResult
from giskard.ml_worker.testing.utils import check_slice_not_empty, validate_classification_label
from giskard.models.base import BaseModel
from . import debug_description_prefix


@test(
    name="Right Label",
    tags=["heuristic", "classification"],
    debug_description=debug_description_prefix + "that <b>do not return the right classification label</b>.",
)
@validate_classification_label
def test_right_label(
    model: BaseModel,
    dataset: Dataset,
    classification_label: str,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.5,
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
    output_ds = list()
    if not passed:
        output_ds.append(dataset.slice(lambda df: df.loc[~dataset.df.index.isin(passed_idx)], row_level=False))
    # ---

    return TestResult(actual_slices_size=[len(dataset)], metric=passed_ratio, passed=passed, output_ds=output_ds)


@test(
    name="Output in range",
    tags=["heuristic", "classification", "regression"],
    debug_description=debug_description_prefix + "that are <b>out of the given range</b>.",
)
@validate_classification_label
def test_output_in_range(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    classification_label: Optional[str] = None,
    min_range: float = 0.3,
    max_range: float = 0.7,
    threshold: float = 0.5,
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
    output_ds = list()
    if not passed:
        output_ds.append(dataset.slice(lambda df: df.loc[~dataset.df.index.isin(passed_idx)], row_level=False))
    # ---

    return TestResult(actual_slices_size=[len(dataset)], metric=passed_ratio, passed=passed, output_ds=output_ds)


@test(
    name="Disparate impact",
    tags=["heuristic", "classification"],
    debug_description=debug_description_prefix + "that are <b>incorrectly predicted on the positive outcome "
    "from both the protected and unprotected slices</b>.",
)
def test_disparate_impact(
    model: BaseModel,
    dataset: Dataset,
    protected_slicing_function: SlicingFunction,
    unprotected_slicing_function: SlicingFunction,
    positive_outcome: str,
    slicing_function: Optional[SlicingFunction] = None,
    min_threshold: float = 0.8,
    max_threshold: float = 1.25,
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
    output_ds = list()
    if not passed:
        failed_protected = list(_protected_predictions != protected_ds.df[dataset.target])
        failed_unprotected = list(_unprotected_predictions != unprotected_ds.df[dataset.target])
        failed_idx_protected = [i for i, x in enumerate(failed_protected) if x]
        failed_idx_unprotected = [i for i, x in enumerate(failed_unprotected) if x]
        output_ds.append(
            dataset.slice(lambda df: df.iloc[failed_idx_protected + failed_idx_unprotected], row_level=False)
        )
    # ---

    return TestResult(metric=disparate_impact_score, passed=passed, messages=messages, output_ds=output_ds)


def _cramer_v(x, y):
    import pandas as pd
    from scipy import stats

    ct = pd.crosstab(x, y)
    return stats.contingency.association(ct, method="cramer")


def _mutual_information(x, y):
    from sklearn.metrics import adjusted_mutual_info_score

    return adjusted_mutual_info_score(x, y)


def _theil_u(x, y):
    import pandas as pd
    from scipy import stats
    from sklearn.metrics import mutual_info_score

    return mutual_info_score(x, y) / stats.entropy(pd.Series(y).value_counts(normalize=True))


@test(
    name="Nominal Association",
    tags=["statistic", "nominal association", "classification"],
    debug_description=debug_description_prefix + "of <b>the data slice that was given as an input of the test</b>.",
)
def test_nominal_association(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: SlicingFunction,
    method: Optional[str] = "theil_u",
    threshold: float = 0.5,
    debug: bool = False,  # noqa: NOSONAR - old version tests will call this under legacy debug mode
):
    """
    Summary: A statistical test for nominal association between the dataset slice and the model predictions. It aims to
    determine whether there is a significant relationship or dependency between the two. It assesses whether the
    observed association is likely to occur by chance or if it represents a true association.

    Description: The general procedure involves setting up a null hypothesis that assumes no association between the
    variables and an alternative hypothesis that suggests an association exists. The statistical test is calculated
    based on three methods: "theil_u", "cramer_v" and "mutual_information".

    Args:
      model(BaseModel):
          Model used to compute the test
      dataset(Dataset):
          Dataset used to compute the test
      slicing_function(SlicingFunction):
          Slicing function to be applied on the dataset
      method(Optional[str]):
          The association test statistic. Choose between "theil_u", "cramer_v", and "mutual_information".
          (default = "theil_u")
      threshold(float):
          Threshold value for the Cramer's V score
      debug(bool):
          legacy debug(deprecated)
    """
    import pandas as pd

    sliced_dataset = dataset.slice(slicing_function)
    check_slice_not_empty(sliced_dataset=sliced_dataset, dataset_name="dataset", test_name="test_nominal_association")

    dx = pd.DataFrame(
        {
            "slice": dataset.df.index.isin(sliced_dataset.df.index).astype(int),
            "prediction": model.predict(dataset).prediction,
        },
        index=dataset.df.index,
    )
    dx.dropna(inplace=True)

    if method == "theil_u":
        metric = _theil_u(dx.slice, dx.prediction)
    elif method == "cramer_v":
        metric = _cramer_v(dx.slice, dx.prediction)
    elif method == "mutual_information":
        metric = _mutual_information(dx.slice, dx.prediction)
    else:
        raise ValueError(
            "Invalid argument value: 'method' argument must " "be 'theil_u', 'cramer_v', or 'mutual_information'"
        )

    passed = metric < threshold

    # --- debug ---
    output_ds = list()
    if not passed:
        output_ds.append(sliced_dataset)
    # ---

    messages = [TestMessage(type=TestMessageLevel.INFO, text=f"metric = {metric}, threshold = {threshold}")]

    return TestResult(metric=metric, passed=passed, messages=messages, output_ds=output_ds)


@test(
    name="Cramer's V",
    tags=["statistic", "nominal association", "classification"],
    debug_description=debug_description_prefix + "of <b>the data slice that was given as an input of the test</b>.",
)
def test_cramer_v(
    model: BaseModel, dataset: Dataset, slicing_function: SlicingFunction, threshold: float = 0.5
) -> TestResult:
    """
    Summary: Cramer's V is a statistical measure used to assess the strength and nature of association between two
    categorical variables. It is an extension of the chi-squared test for independence and takes into account the
    dimensions of the contingency table. Cramer's V ranges from 0 to 1, where 0 indicates no association and 1
    indicates a perfect association.

    Description: Cramer's V is particularly useful for analyzing nominal data and understanding the relationship between
    categorical variables. It's a normalized version of the chi-squared statistic that considers the dimensions of the
    contingency table. The formula adjusts for the number of observations and the number of categories in the
    variables to provide a more interpretable measure of association.
    Mathematically, the Cramer's V metric can be expressed as:

    .. math::

      V = \sqrt{\\frac{\chi^2}{n \cdot \min(k-1, r-1)}}

    where: :math:`\chi^2` is the chi-squared statistic for the two variables. n is the total number of observations.
    :math:`k` is the
    number of categories in one variable. :math:`r` is the number of categories in the other variable.

    Args:
      model(BaseModel):
          Model used to compute the test
      dataset(Dataset):
          Dataset used to compute the test
      slicing_function(SlicingFunction):
          Slicing function to be applied on the dataset
      threshold(float):
          Threshold value for the Cramer's V score
    """
    return test_nominal_association(model, dataset, slicing_function, "cramer_v", threshold).execute()


@test(
    name="Mutual Information",
    tags=["statistic", "nominal association", "classification"],
    debug_description=debug_description_prefix + "of <b>the data slice that was given as an input of the test</b>.",
)
def test_mutual_information(
    model: BaseModel, dataset: Dataset, slicing_function: SlicingFunction, threshold: float = 0.5
) -> TestResult:
    """
    Summary: The mutual information statistical test is a measure used to quantify the degree of association between two
    categorical variables. It assesses how much information about one variable can be gained from knowing the other
    variable's value. Mutual information is based on the concept of entropy and provides a way to determine the level
    of dependency or correlation between categorical variables.

    Description: Mutual information measures the reduction in uncertainty about one variable given knowledge of the
    other variable. It takes into account both individual and joint distributions of the variables and provides a value
    indicating how much information is shared between them. Higher mutual information values suggest stronger
    association, while lower values indicate weaker or no association.
    Mathematically, the mutual information metric can be expressed as:

    .. math::

      I(X;Y) = \sum_{x \in X} \sum_{y \in Y} p(x, y) \cdot \log ( \\frac{p(x, y)}{p(x) \cdot p(y)})

    where: :math:`p(x,y)` is the joint probability mass function of variables :math:`X` and :math:`Y`. :math:`p(x)` and
    :math:`p(y)` are the marginal probability mass functions of variables :math:`X` and :math:`Y` respectively.

    Args:
      model(BaseModel):
          Model used to compute the test
      dataset(Dataset):
          Dataset used to compute the test
      slicing_function(SlicingFunction):
          Slicing function to be applied on the dataset
      threshold(float):
          Threshold value for the mutual information score
    """
    return test_nominal_association(model, dataset, slicing_function, "mutual_information", threshold).execute()


@test(
    name="Theil's U",
    tags=["statistic", "nominal association", "classification"],
    debug_description=debug_description_prefix + "of <b>the data slice that was given as an input of the test</b>.",
)
def test_theil_u(
    model: BaseModel, dataset: Dataset, slicing_function: SlicingFunction, threshold: float = 0.5
) -> TestResult:
    """
    Summary: Theil's U statistical test for nominal association is a measure used to assess the strength and direction
    of association between two categorical variables. It quantifies the inequality in the distribution of one variable
    relative to the distribution of the other variable, providing insights into the pattern of association between
    them. Theil's U ranges from 0 to 1, where 0 indicates no association, and 1 indicates a perfect association.

    Description: Theil's U for nominal association is commonly used to analyze the relationships between variables like
    ethnicity, gender, or occupation. It considers the proportions of one variable's categories within each category of
    the other variable. The calculation involves comparing the observed joint distribution of the two variables with
    what would be expected if there were no association.
    Mathematically, Theil's U for nominal association can be expressed as:

    .. math::

      U = \\frac{H(x|y) - H(y|x)}{H(x)}

    where :math:`H(x|y)`, :math:`H(y|x)` are the conditional entropies of the two variables and :math:`H(x)` is the
    entropy of the first variable.

    Args:
      model(BaseModel):
          Model used to compute the test
      dataset(Dataset):
          Dataset used to compute the test
      slicing_function(SlicingFunction):
          Slicing function to be applied on the dataset
      threshold(float):
          Threshold value for the Theil's U score
    """
    return test_nominal_association(model, dataset, slicing_function, "theil_u", threshold).execute()
