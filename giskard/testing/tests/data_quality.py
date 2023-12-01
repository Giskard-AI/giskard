from giskard.ml_worker.testing.test_result import TestResult
from giskard.ml_worker.testing.registry.decorators import test
from giskard.datasets.base import Dataset
import pandas as pd

@test(name="Data Uniqueness Test")
def uniqueness_test(dataset: Dataset, column: str):
    column_data = dataset.df[column]
    uniqueness_ratio = len(column_data.unique()) / len(column_data)
    return TestResult(passed=uniqueness_ratio == 1)

@test(name="Data Completeness Test")
def completeness_test(dataset: Dataset):
    completeness_scores = {}
    for column in dataset.df.columns:
        column_data = dataset.df[column]
        completeness_ratio = len(column_data.dropna()) / len(column_data)
        completeness_scores[column] = completeness_ratio
    return completeness_scores


# Testing the uniqueness test
dataset = Dataset(pd.DataFrame({'test': [1, 2, None, 2, 4, None]}))

print(completeness_test(dataset).execute())