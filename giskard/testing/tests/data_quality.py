"""
Module for data quality tests.
"""
from typing import Iterable, List, Optional

from collections import Counter, defaultdict

import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from giskard.core.test_result import TestMessage, TestMessageLevel, TestResult
from giskard.datasets.base import Dataset
from giskard.registry.decorators import test


@test(name="Data uniqueness test", tags=["data"])
def test_data_uniqueness(dataset: Dataset, column: str, threshold: float = 0.8) -> TestResult:
    """Test for checking the uniqueness of data in a column.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test.
    column : str
        The column to check for uniqueness.
    threshold : float, optional
        The minimum uniqueness ratio for the test to pass., by default 0.8

    Returns
    -------
    TestResult
        The result of the test.
    """
    column_data = dataset.df[column]
    uniqueness_ratio = len(column_data.unique()) / len(column_data)

    return TestResult(passed=uniqueness_ratio >= threshold, metric=uniqueness_ratio, metric_name=f"{column} uniqueness")


@test(name="Data completeness test", tags=["data"])
def test_data_completeness(dataset: Dataset, column_name: str, threshold: float) -> TestResult:
    """Test for checking the completeness of data in a dataset.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test.
    column_name : str
        The name of the column to test.
    threshold : float
        The minimum completeness ratio for the test to pass.

    Returns
    -------
    TestResult
        A TestResult object indicating whether the test passed and the completeness ratio.
    """
    output_ds = dataset.slice(lambda df: df[df[column_name].isnull()], row_level=False)
    completeness_ratio = 1 - len(output_ds.df) / len(dataset.df)
    passed = completeness_ratio >= threshold

    return TestResult(
        passed=passed, metric=completeness_ratio, metric_name=f"{column_name} completeness", output_ds=[output_ds]
    )


@test(name="Data validation (valid range)", tags=["data"])
def test_valid_range(dataset: Dataset, column: str, min_value: float = None, max_value: float = None) -> TestResult:
    """Test for checking if data in a column falls within a specified range.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    column : str
        The column to check
    min_value : float, optional
        The minimum valid value, by default None
    max_value : float, optional
        The maximum valid value, by default None

    Returns
    -------
    TestResult
        The result of the test
    """
    if min_value is not None and max_value is not None:
        output_ds = dataset.slice(lambda df: df[(min_value > df[column]) | (df[column] > max_value)], row_level=False)
    elif min_value is not None:
        output_ds = dataset.slice(lambda df: df[min_value > df[column]], row_level=False)
    elif max_value is not None:
        output_ds = dataset.slice(lambda df: df[df[column] > max_value], row_level=False)
    else:
        raise ValueError("Neither min_value nor max_value were provided")

    test_passed = len(output_ds.df.index) == 0

    return TestResult(
        passed=test_passed, metric_name="Out of range", metric=len(output_ds.df.index), output_ds=[output_ds]
    )


@test(name="Data validation (valid values)", tags=["data"])
def test_valid_values(dataset: Dataset, column: str, valid_values: Optional[List] = None) -> TestResult:
    """Test for checking if data in a column is in a set of valid values.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    column : str
        The column to check
    valid_values : Optional[List], optional
        A list of valid values, by default None

    Returns
    -------
    TestResult
        The result of the test
    """
    if valid_values is None:
        raise ValueError("valid_values must be provided")

    output_ds = dataset.slice(lambda df: df[~df[column].isnull() & ~df[column].isin(valid_values)], row_level=False)
    test_passed = len(output_ds.df.index) == 0

    return TestResult(
        passed=test_passed, metric=len(output_ds.df.index), metric_name="Invalid values", output_ds=[output_ds]
    )


@test(name="Data correlation test", tags=["data"])
def test_data_correlation(
    dataset: Dataset,
    column1: str = None,
    column2: str = None,
    should_correlate: bool = True,
    correlation_threshold: float = 0.0,
) -> TestResult:
    """Test for analyzing correlations between two specific features.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    column1 : str, optional
        The first column to check, by default None
    column2 : str, optional
        The second column to check, by default None
    should_correlate : bool, optional
        Whether the two columns should correlate, by default True
    correlation_threshold : float, optional
        The minimum absolute correlation that is considered significant, by default 0.0

    Returns
    -------
    TestResult
        The result of the test, containing the correlation between the two columns
    """
    # Calculate the correlation between the two columns
    correlation = dataset.df[column1].corr(dataset.df[column2])

    # Check if the absolute correlation is above the threshold and the correlation is as expected
    if should_correlate:
        test_passed = correlation >= correlation_threshold
    else:
        test_passed = correlation < correlation_threshold

    return TestResult(passed=bool(test_passed), metric_name="correlation", metric=correlation)


@test(name="Outlier value test", tags=["data"])
def test_outlier_value(dataset: Dataset, column: str, eps: float = 0.5, min_samples: int = 5) -> TestResult:
    """Test for identifying outliers or anomalies in a column of the dataset using DBSCAN.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    column : str
        The column to check for anomalies
    eps : float, optional
        The maximum distance between two samples for one to be considered as in the neighborhood of the other, by default 0.5
    min_samples : int, optional
        The number of samples in a neighborhood for a point to be considered as a core point, by default 5

    Returns
    -------
    TestResult
        The result of the test, containing the indices of the anomalies
    """
    column_data = dataset.df[column].values.reshape(-1, 1)
    model = DBSCAN(eps=eps, min_samples=min_samples)
    model.fit(column_data)
    preds = model.labels_
    anomalies = [i for i, pred in enumerate(preds) if pred == -1]

    return TestResult(passed=len(anomalies) == 0, metric=len(anomalies), metric_name="anomalies")


@test(name="Foreign constraint test", tags=["data"])
def test_foreign_constraint(
    dataset: Dataset, column: str, target_dataset: Dataset, target_column: str, threshold: float = 0.0
) -> TestResult:
    """Ensure that all data in a column of one dataset are present in a column of another dataset.

    Parameters
    ----------
    dataset : Dataset
        The dataset to check
    column : str
        The column in the dataset to check
    target_dataset : Dataset
        The dataset to compare against
    target_column : str
        The column in the target dataset to compare against
    threshold : float, optional
        The maximum allowed ratio of missing values, by default 0.0

    Returns
    -------
    TestResult
        The result of the test, indicating whether the test passed and the ratio of missing values
    """
    output_ds = dataset.slice(
        lambda df: df[~dataset.df[column].isin(target_dataset.df[target_column].unique())], row_level=False
    )

    missing_ratio = len(output_ds.df.index) / len(dataset.df.index)

    return TestResult(
        passed=missing_ratio <= threshold, metric=missing_ratio, metric_name="missing ratio", output_ds=[output_ds]
    )


@test(name="Label consistency test", tags=["data"])
def test_label_consistency(dataset: Dataset, label_column: str) -> TestResult:
    """Test for checking the consistency of datatype across each label throughout dataset.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    label_column : str
        The column containing the labels

    Returns
    -------
    TestResult
        The result of the test
    """
    # Group the dataset by the label column
    groups = defaultdict(list)
    for _, row in dataset.df.iterrows():
        groups[row[label_column]].append(row)

    # Check that all data in each group is of the same type
    inconsistencies = []
    for label, group in groups.items():
        types_in_group = {type(val) for row in group for col, val in row.items() if col != label_column}
        if len(types_in_group) > 1:
            inconsistencies.append((label, types_in_group))

    if inconsistencies:
        message = f"Inconsistencies found: {inconsistencies}"
        return TestResult(passed=False, metric_name="consistency", metric=0, messages=message)

    return TestResult(passed=True, metric_name="consistency", metric=1)


@test(name="Mislabeling test", tags=["data"])
def test_mislabeling(dataset: Dataset, labelled_column: str, reference_columns: Iterable[str]) -> TestResult:
    """Test for detecting mislabelled data

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    labelled_column : str
        The column containing the labels
    reference_columns : Iterable[str]
        The columns containing the data to check for consistency

    Returns
    -------
    TestResult
        The result of the test, containing the indices of the mislabelled data
    """
    # Copy the dataset to avoid changing the original data
    dataset_copy = dataset.df.copy()

    # Encode the categorical data
    le = LabelEncoder()
    for column in dataset_copy.columns:
        if dataset_copy[column].dtype == "object":
            dataset_copy[column] = le.fit_transform(dataset_copy[column])

    # Prepare the data
    x = dataset_copy[list(reference_columns)]
    y = dataset_copy[labelled_column]

    # Combine the data and labels
    data = pd.concat([x, y], axis=1)

    # Train the Isolation Forest model
    model = IsolationForest(contamination=0.1)
    model.fit(data)

    # Predict the anomalies in the data
    anomalies = model.predict(data) == -1

    # Check if any of the anomalies have different labels
    mislabelled_data = dataset.slice(lambda df: df[anomalies], row_level=False)

    return TestResult(
        passed=len(mislabelled_data.df.index) == 0,
        metric_name="mislabelled",
        metric=len(mislabelled_data.df.index),
        output_ds=[mislabelled_data],
    )


@test(name="Feature importance test", tags=["data"])
def test_feature_importance(
    dataset: Dataset, feature_columns: Iterable[str], target_column: str, importance_threshold: float = 0
) -> TestResult:
    """Test for analyzing the importance of features in a classification problem

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    feature_columns : Iterable[str]
        The columns containing the features
    target_column : str
        The column containing the target variable
    importance_threshold : float, optional
        The minimum importance that is considered significant, by default 0

    Returns
    -------
    TestResult
        The result of the test, containing the feature importances
    """
    features = list(feature_columns)
    x = dataset.df[features]
    y = dataset.df[target_column]
    # Train the Random Forest model
    model = RandomForestClassifier()
    model.fit(x, y)
    # Get the feature importances
    importances = model.feature_importances_
    feature_importances = dict(zip(features, importances))
    # Check if the importance of all features is above the threshold
    test_passed = all(importance >= importance_threshold for importance in importances)
    # Create a message containing the feature importances
    message = TestMessage(text=f"Feature importances: \n{feature_importances}", type=TestMessageLevel.INFO)

    return TestResult(passed=test_passed, metric_name="feature_importance", metric=importances, messages=[message])


@test(name="Class imbalance test", tags=["data"])
def test_class_imbalance(
    dataset: Dataset, target_column: str, lower_threshold: float, upper_threshold: float
) -> TestResult:
    """Test for assessing the distribution of classes in classification problems.

    Parameters
    ----------
    dataset : Dataset
        The dataset to test
    target_column : str
        The column containing the target variable
    lower_threshold : float
        The minimum allowed class proportion
    upper_threshold : float
        The maximum allowed class proportion

    Returns
    -------
    TestResult
        The result of the test, containing the class proportions
    """
    # Convert classes to strings and calculate the class proportions
    class_counts = Counter(dataset.df[target_column].astype(str))
    total_count = len(dataset.df)
    class_proportions = {cls: count / total_count for cls, count in class_counts.items()}

    # Check if any class proportion is below the lower threshold or above the upper threshold
    passed = all(lower_threshold <= proportion <= upper_threshold for proportion in class_proportions.values())

    # Create a message containing the class proportions
    message = TestMessage(text=f"Class proportions: \n{class_proportions}", type=TestMessageLevel.INFO)

    return TestResult(passed=passed, metric_name="class_proportion", metric=class_proportions, messages=[message])
