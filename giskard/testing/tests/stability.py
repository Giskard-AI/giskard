from typing import List, Optional

import numpy as np

from giskard import Dataset, TestResult, test
from giskard.models.base import BaseModel
from giskard.testing.tests.debug_slicing_functions import row_failing_slicing_fn


def _check_features(feature_names, feature_values, model, dataset):
    if not all(elem in model.feature_names for elem in feature_names):
        raise ValueError("feature_names must only contain only from model.feature_names")

    if feature_values is None:
        for feature_name in feature_names:
            if dataset.column_types[feature_name] != "numeric":
                raise ValueError(f"Please provide values for non numeric feature {feature_name}")
        return

    if set(feature_names) != set(feature_values.keys()):
        raise ValueError("feature_values keys should be the same as feature_names")

    lengths = [len(elt) for elt in list(feature_values.values())]
    if not all(x == lengths[0] for x in lengths):
        raise ValueError("feature_values must contain elements with same length")


def _check_classif_index(model, classif_index_label):
    if model.is_classification and classif_index_label >= len(model.classification_labels):
        raise ValueError("classif_index should be smaller than model.classification_labels")


def _get_predictions(
    model: BaseModel,
    dataset: Dataset,
    feature_names: List[str],
    feature_values: Optional[dict] = None,
    random_state: int = 123456,
    num_samples: int = 100,
    num_grid: int = 50,
    classif_index_label: int = 0,
):
    # Create grids of values per column if not passed as input
    if feature_values is None:
        feature_values = {}
        for col_name in feature_names:
            min_col = dataset.df[col_name].min()
            max_col = dataset.df[col_name].max()

            # Create grid of values between min and max
            feature_values[col_name] = np.linspace(min_col, max_col, num_grid)
    else:
        num_grid = len(list(feature_values.values())[0])

    # Generate data from existing rows by modifying the value of the column of interest
    augmented_ds = []
    sample_rows = dataset.df.sample(n=num_samples, random_state=random_state)
    for i in range(num_grid):
        sample_rows_copy = sample_rows.copy()
        for col_name in feature_names:
            sample_rows_copy.loc[:, col_name] = feature_values[col_name][i].astype(dataset.df.dtypes[col_name])
        augmented_ds.append(
            Dataset(
                sample_rows_copy,
                target=dataset.target,
                cat_columns=dataset.cat_columns,
                column_types=dataset.column_types,
                validation=False,
            )
        )

    # Predictions
    predictions = []
    for current_dataset in augmented_ds:
        predictions.append(model.predict(current_dataset).raw)
    predictions = np.array(predictions)

    # If classification, select the right index in the last dimension
    if model.is_classification:
        predictions = predictions[:, :, classif_index_label]

    return predictions, sample_rows


@test(name="Monotonicity", tags=["monotonicity"])
def test_monotonicity(
    model: BaseModel,
    dataset: Dataset,
    feature_names: List[str],
    feature_values: Optional[dict] = None,
    increasing: bool = True,
    random_state: int = 123456,
    num_samples: int = 100,
    num_grid: int = 50,
    classif_index_label: int = 0,
):
    """Test if the model is monotonic for a given column name by selecting random samples from
    the dataset and augmenting them with different values for the specified column

    Parameters
    ----------
    model : BaseModel
        Model used to compute the test
    dataset : Dataset
        Actual dataset used to compute the test
    feature_names : List[str]
        Column names to test (at the same time)
    feature_values : Optional[dict]
        Values to test for each column, the values should always have the same length
    increasing : bool
        Whether to test for increasing or decreasing monotonicity
    random_state : int
        Random state for sampling
    num_samples : int
        Number of samples from which generate the grid and test
    num_grid : int
        Number of points in the grid of values for the colum
    classif_index_label : int
        If classification, which index to consider for the test

    Returns
    -------
    TestResult
        The test result.
    """

    _check_features(feature_names=feature_names, feature_values=feature_values, model=model, dataset=dataset)
    _check_classif_index(model=model, classif_index_label=classif_index_label)

    # Get predictions
    predictions, sample_rows = _get_predictions(
        model=model,
        dataset=dataset,
        feature_names=feature_names,
        feature_values=feature_values,
        random_state=random_state,
        num_samples=num_samples,
        num_grid=num_grid,
        classif_index_label=classif_index_label,
    )

    # Check for monotonicity
    if increasing:
        passed = np.diff(predictions, axis=0) >= 0
    else:
        passed = np.diff(predictions, axis=0) <= 0

    # --- debug ---
    output_ds = list()
    if not passed.all():
        output_ds.append(dataset.slice(row_failing_slicing_fn(index_failure=sample_rows.index[~passed.all(axis=0)])))
    # ---

    return TestResult(passed=passed.all(), output_ds=output_ds, metric=(~passed).mean())


@test(name="Smoothness", tags=["smoothness"])
def test_smoothness(
    model: BaseModel,
    dataset: Dataset,
    feature_names: List[str],
    feature_values: Optional[dict] = None,
    random_state: int = 123456,
    num_samples: int = 100,
    num_grid: int = 50,
    classif_index_label: int = 0,
    threshold: float = 2,
    ord: int = 2,
    ref_function: Optional[np.ndarray] = None,
):
    """Test if the model is smooth with respect to given columns.
    The smoothness score is computed as follows
    $$S(y) = \frac{1}{N} \\sum_{i=1}^N (y_{i-1} - 2y_i + y_{i+1})^2$$

    Then a ratio $$S(y) / S(y_{\text{ref}})$$, where $$y_{\text{ref}}$$ is given through ref_function,
    is compared to the threshold in log value. If ref_functino is None, $$S(y_{\text{ref}}) = 1$$

    Parameters
    ----------
    model : BaseModel
        Model used to compute the test
    dataset : Dataset
        Actual dataset used to compute the test
    feature_names : List[str]
        Column names to test (at the same time)
    feature_values : Optional[dict]
        Values to test for each column, the values should always have the same length
    random_state : int
        Random state for sampling
    num_samples : int
        Number of samples from which generate the grid and test
    num_grid : int
        Number of points in the grid of values for the colum
    classif_index_label : int
        If classification, which index to consider for the test
    threshold : float
        Threshold over which the test is failed
    ord : int
        Order of the norm used to evaluate smoothness
    ref_function : np.ndarray
        Function values to compare to

    Returns
    -------
    TestResult
        The test result.
    """

    _check_features(feature_names=feature_names, feature_values=feature_values, model=model, dataset=dataset)
    _check_classif_index(model=model, classif_index_label=classif_index_label)

    # Get predictions
    predictions, sample_rows = _get_predictions(
        model=model,
        dataset=dataset,
        feature_names=feature_names,
        feature_values=feature_values,
        random_state=random_state,
        num_samples=num_samples,
        num_grid=num_grid,
        classif_index_label=classif_index_label,
    )

    # Check smoothness with respect to ref (sin)
    if ref_function is None:
        ref_score = 1
    elif ord == 2:
        ref_score = np.mean((ref_function[:-2] - 2 * ref_function[1:-1] + ref_function[2:]) ** 2)
    else:
        ref_score = np.abs(ref_function[1:] - ref_function[:-1]).mean()
    if ord == 2:
        scores = np.log10(
            np.mean((predictions[:-2, :] - 2 * predictions[1:-1, :] + predictions[2:, :]) ** 2, axis=0) / ref_score
            + 1e-20
        )
    elif ord == 1:
        scores = np.log10(np.abs(predictions[1:, :] - predictions[:-1, :]).mean(axis=0) / ref_score + 1e-20)

    passed = scores < threshold

    # --- debug ---
    output_ds = list()
    if not passed.all():
        output_ds.append(dataset.slice(row_failing_slicing_fn(index_failure=sample_rows.index[~passed])))
    # ---

    return TestResult(passed=passed.all(), output_ds=output_ds, metric=scores.max())
