"""
Module for data quality tests.
"""
import pandas as pd
from giskard.ml_worker.testing.test_result import TestResult
from giskard.ml_worker.testing.registry.decorators import test
from giskard.datasets.base import Dataset

@test(name="Data Uniqueness Test")
def uniqueness_test(dataset: Dataset, column: str):
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
    return TestResult(passed=uniqueness_ratio == 1)

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


# data = {
#     'column1': [1, 2, 3, 4, 5, None, 7, 8, None, 10],
#     'column2': ['a', 'b', 'c', 'd', None, 'f', 'g', 'h', 'i', 'j'],
#     'column3': [1.1, None, 3.3, 4.4, 5.5, 6.6, None, 8.8, 9.9, 10.1],
#     'column4': [None, None, None, None, None, None, None, None, None, None],
# }
# df = pd.DataFrame(data)

# # Create a Dataset from the DataFrame
# dataset = Dataset(df)
# print(completeness_test(dataset).execute())