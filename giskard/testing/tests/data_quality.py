"""
Module for data quality tests.
"""
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
    return TestResult(passed=uniqueness_ratio >= threshold, metric=uniqueness_ratio)

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
    return completeness_scores

@test(name="Data Range and Validity Test")
def range_validity_test(dataset: Dataset, column: str, min_value=None, max_value=None, valid_values=None):
    """
    Test for checking if data in a column falls within a specified range or set of valid values.

    Args:
        dataset (Dataset): The dataset to test.
        column (str): The column to check.
        min_value (float, optional): The minimum valid value. Defaults to None.
        max_value (float, optional): The maximum valid value. Defaults to None.
        valid_values (list, optional): A list of valid values. Defaults to None.

    Returns:
        TestResult: The result of the test.
    """
    column_data = dataset.df[column]
    if valid_values is not None:
        # Check if all values are in the list of valid values
        test_passed = all(x in valid_values for x in column_data.dropna())
    else:
        # Check if all values are within the specified range
        test_passed = all(min_value <= x <= max_value for x in column_data.dropna())
    return TestResult(passed=test_passed)
