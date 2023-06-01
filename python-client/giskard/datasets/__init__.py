from typing import Dict, Optional, List
import pandas as pd
from giskard.datasets.base import Dataset
from giskard.core.validation import configured_validate_arguments


@configured_validate_arguments
def wrap_dataset(dataset: pd.DataFrame,
                 name: Optional[str] = None,
                 target: Optional[str] = None,
                 cat_columns: Optional[List[str]] = None,
                 infer_column_types: Optional[bool] = False,
                 column_types: Optional[Dict[str, str]] = None):
    """
    A function that wraps a Pandas DataFrame into a Giskard Dataset object, with optional validation of input arguments.

    Args:
        dataset (pd.DataFrame):
            A Pandas DataFrame containing the data to be wrapped.
        name (Optional[str]):
            A string representing the name of the dataset (default None).
        target (Optional[str]):
            A string representing the name of the target variable (default None).
        cat_columns (Optional[List[str]]):
            A list of strings representing the names of categorical columns (default None).
        infer_column_types (Optional[bool]):
            A boolean indicating whether to infer column types automatically (default False).
        column_types (Optional[Dict[str, str]]):
            A dictionary representing column names and their types (default None).

    Returns:
        Dataset:
            A Giskard Dataset object that wraps the input Pandas DataFrame.

    Raises:
        TypeError:
            If the input dataset is not a Pandas DataFrame or if cat_columns is not a list of strings.
    """

    print("Your 'pandas.DataFrame' dataset is successfully wrapped by Giskard's 'Dataset' wrapper class.")
    return Dataset(dataset,
                   name,
                   target,
                   cat_columns,
                   infer_column_types,
                   column_types)
