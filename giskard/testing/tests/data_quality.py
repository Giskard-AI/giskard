"""
Module for data quality tests.
"""
from collections import Counter, defaultdict
from typing import Iterable
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from giskard.ml_worker.testing.test_result import TestResult
from giskard.ml_worker.testing.registry.decorators import test
from giskard.datasets.base import Dataset

@test(name="Data Uniqueness Test")
def uniqueness_test(dataset: Dataset, column: str, threshold: float = 0.8):
    """
    Test for checking the uniqueness of data in a column.

    Args:
        dataset (Dataset): The dataset to test.
        column (str): The column to check for uniqueness.

    Returns:
        TestResult: The result of the test.
    """
    column_data = dataset.df[column]
    uniqueness_ratio = len(column_data.unique()) / len(column_data)
    return TestResult(passed=uniqueness_ratio >= threshold,
                      metric=uniqueness_ratio, metric_name="uniqueness")

@test(name="Data Completeness Test")
def completeness_test(dataset: Dataset):
    """
    Test for checking the completeness of data in a dataset.

    Args:
        dataset (Dataset): The dataset to test.

    Returns:
        dict: A dictionary with the completeness score for each column.
    """
    completeness_scores = {}
    for column in dataset.df.columns:
        column_data = dataset.df[column]
        completeness_ratio = len(column_data.dropna()) / len(column_data)
        completeness_scores[column] = completeness_ratio
    return TestResult(messages=completeness_scores)

@test(name="Data Range Test")
def range_test(dataset: Dataset, column: str, min_value=None, max_value=None):
    """
    Test for checking if data in a column falls within a specified range.

    Args:
        dataset (Dataset): The dataset to test.
        column (str): The column to check.
        min_value (float, optional): The minimum valid value. Defaults to None.
        max_value (float, optional): The maximum valid value. Defaults to None.

    Returns:
        TestResult: The result of the test.
    """
    column_data = dataset.df[column]
    if min_value is not None and max_value is not None:
        test_passed = all(min_value <= x <= max_value for x in column_data.dropna())
    elif min_value is not None:
        test_passed = all(min_value <= x for x in column_data.dropna())
    elif max_value is not None:
        test_passed = all(x <= max_value for x in column_data.dropna())
    else:
        raise ValueError("Neither min_value nor max_value were provided")
    return TestResult(passed=test_passed)

@test(name="Data Validity Test")
def validity_test(dataset: Dataset, column: str, valid_values=None):
    """
    Test for checking if data in a column is in a set of valid values.

    Args:
        dataset (Dataset): The dataset to test.
        column (str): The column to check.
        valid_values (list, optional): A list of valid values. Defaults to None.

    Returns:
        TestResult: The result of the test.
    """
    if valid_values is None:
        raise ValueError("valid_values must be provided")
    column_data = dataset.df[column]
    test_passed = all(x in valid_values for x in column_data.dropna())
    return TestResult(passed=test_passed)

@test(name="Data Correlation Test")
def correlation_test(dataset: Dataset,
                     column1: str = None,
                     column2: str = None,
                     should_correlate: bool = True,
                     correlation_threshold: float = 0):
    """
    Test for analyzing correlations between two specific features.

    Args:
        dataset (Dataset): The dataset to test.
        column1 (str, optional): The first column to check. Defaults to None.
        column2 (str, optional): The second column to check. Defaults to None.
        should_correlate (bool, optional): Whether
        the two columns should correlate. Defaults to True.
        correlation_threshold (float, optional): The minimum absolute
        correlation that is considered significant. Defaults to 0.

    Returns:
        TestResult: The result of the test, containing the correlation between the two columns.
    """
    # Calculate the correlation between the two columns
    correlation = dataset.df[column1].corr(dataset.df[column2])

    # Check if the absolute correlation is above the threshold and the correlation is as expected
    test_passed = (abs(correlation) >=
                   correlation_threshold) and ((correlation > 0) == should_correlate)

    return TestResult(passed=test_passed, metric_name="correlation", metric=correlation)

@test(name="Data Outlier Detection Test")
def outlier(dataset: Dataset, column: str, eps: float = 0.5, min_samples: int = 5):
    """
    Test for identifying outliers or anomalies in a column of the dataset using DBSCAN.

    Args:
        dataset (Dataset): The dataset to test.
        column (str): The column to check for anomalies.
        eps (float): The maximum distance between two
        samples for one to be considered as in the neighborhood of the other.
        min_samples (int): The number of samples in a neighborhood
        for a point to be considered as a core point.

    Returns:
        TestResult: The result of the test, containing the indices of the anomalies.
    """
    column_data = dataset.df[column].values.reshape(-1, 1)
    model = DBSCAN(eps=eps, min_samples=min_samples)
    model.fit(column_data)
    preds = model.labels_
    anomalies = [i for i, pred in enumerate(preds) if pred == -1]
    return TestResult(passed=len(anomalies) == 0, messages=anomalies)

@test(name="Ensure all exists")
def ensure_all_exists(dataset: Dataset, column: str,
                      target_dataset: Dataset,
                      target_column: str,
                      threshold: float = 0.0):
    """
    Ensure that all data in a column of one dataset are present in a column of another dataset.

    Args:
        dataset (Dataset): The dataset to check.
        column (str): The column in the dataset to check.
        target_dataset (Dataset): The dataset to compare against.
        target_column (str): The column in the target dataset to compare against.
        threshold (float, optional): The maximum allowed ratio of missing values. Defaults to 0.0.

    Returns:
        TestResult: The result of the test, indicating whether
        the test passed and the ratio of missing values.
    """
    source = dataset.df[column]
    referenced = target_dataset.df[target_column]
    not_included = source[~source.isin(referenced)]
    missing_ratio = len(not_included) / len(source)
    return TestResult(passed=missing_ratio <= threshold, metric=missing_ratio)

@test(name="Label Consistency Test")
def label_consistency_test(dataset: Dataset, label_column: str):
    """
    Test for checking the consistency of datatype across each label throughout dataset.

    Args:
        dataset (Dataset): The dataset to test.
        label_column (str): The column containing the labels.

    Returns:
        TestResult: The result of the test.
    """
    # Group the dataset by the label column
    groups = defaultdict(list)
    for _, row in dataset.df.iterrows():
        groups[row[label_column]].append(row)

    # Check that all data in each group is of the same type
    inconsistencies = []
    for label, group in groups.items():
        types_in_group = {type(val) for row in group for col,
                          val in row.items() if col != label_column}
        if len(types_in_group) > 1:
            inconsistencies.append((label, types_in_group))

    if inconsistencies:
        message = f"Inconsistencies found: {inconsistencies}"
        return TestResult(passed=False, metric_name="consistency", metric=0, messages=message)

    return TestResult(passed=True, metric_name="consistency", metric=1)

@test(name="Mislabeled Data Test")
def mislabel(dataset: Dataset, labelled_column: str, reference_columns: Iterable[str]):
    """
    Test for detecting mislabelled data.

    Args:
        dataset (giskard.Dataset): The dataset to test.
        labelled_column (str): The column containing the labels.
        reference_columns (Iterable[str]): The columns containing the data to check for consistency.

    Returns:
        TestResult: The result of the test, containing the indices of the mislabelled data.
    """
    # Copy the dataset to avoid changing the original data
    dataset_copy = dataset.df.copy()

    # Encode the categorical data
    le = LabelEncoder()
    for column in dataset_copy.columns:
        if dataset_copy[column].dtype == 'object':
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
    mislabelled_data = dataset.df[anomalies]

    if not mislabelled_data.empty:
        message = f"Mislabelled data found: \n{mislabelled_data}"
        return TestResult(passed=False, metric_name="consistency", metric=0, messages=message)

    return TestResult(passed=True, metric_name="consistency", metric=1)

@test(name="Feature Importance Test")
def feature_importance_test(dataset: Dataset,
                            feature_columns: Iterable[str],
                            target_column: str,
                            importance_threshold: float = 0):
    """
    Test for analyzing the importance of features in a classification problem.

    Args:
        dataset (Dataset): The dataset to test.
        feature_columns (List[str]): The columns containing the features.
        target_column (str): The column containing the target variable.
        importance_threshold (float, optional): The minimum importance
        that is considered significant. Defaults to 0.

    Returns:
        TestResult: The result of the test, containing the feature importances.
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
    message = f"Feature importances: \n{feature_importances}"

    return TestResult(passed=test_passed,
                      metric_name="feature_importance",
                      metric=importances,
                      messages=message)

@test(name="Class Imbalance Test")
def class_imbalance(dataset: Dataset,
                    target_column: str,
                    lower_threshold: float,
                    upper_threshold: float):
    """
    Test for assessing the distribution of classes in classification problems.

    Args:
        dataset (giskard.Dataset): The dataset to test.
        target_column (str): The column containing the target variable.
        lower_threshold (float): The minimum allowed class proportion.
        upper_threshold (float): The maximum allowed class proportion.

    Returns:
        TestResult: The result of the test, containing the class proportions.
    """
    # Convert classes to strings and calculate the class proportions
    class_counts = Counter(dataset.df[target_column].astype(str))
    total_count = len(dataset.df)
    class_proportions = {cls: count / total_count for cls, count in class_counts.items()}

    # Check if any class proportion is below the lower threshold or above the upper threshold
    passed = all(lower_threshold <=
                 proportion <= upper_threshold
                 for proportion in class_proportions.values())

    # Create a message containing the class proportions
    message = f"Class proportions: \n{class_proportions}"

    return TestResult(passed=passed,
                      metric_name="class_proportion",
                      metric=class_proportions,
                      messages=message)
