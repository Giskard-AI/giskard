"""
Module for data quality tests.
"""
from sklearn.cluster import DBSCAN
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
    return TestResult(passed=uniqueness_ratio >= threshold, metric=uniqueness_ratio, metric_name="uniqueness")

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
def correlation_test(dataset: Dataset, column1: str = None, column2: str = None):
    """
    Test for analyzing correlations between two specific features.

    Args:
        dataset (Dataset): The dataset to test.
        column1 (str, optional): The first column to check. Defaults to None.
        column2 (str, optional): The second column to check. Defaults to None.

    Returns:
        TestResult: The result of the test,
        containing the correlation between the two columns
        (if provided) or the full correlation matrix.
    """
    correlation_matrix = dataset.df.corr()

    if column1 is not None and column2 is not None:
        correlation = dataset.df[[column1, column2]].corr().iloc[0, 1]
        return TestResult(passed=True,
                          metric=correlation,
                          metric_name="correlation",
                          messages=correlation_matrix)
    else:
        return TestResult(passed=True,
                          metric=None,
                          metric_name="correlation",messages=correlation_matrix)

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
def ensure_all_exists(dataset: Dataset, column: str, target_dataset: Dataset, target_column: str, threshold: float = 0.0):
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
