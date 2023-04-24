from typing import Dict, Optional, List

import pandas as pd

from giskard.core.validation import configured_validate_arguments
from giskard.datasets.base import Dataset


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
            A Pandas dataframe that contains some data examples that might interest you to inspect (test set, train set,
            production data). Some important remarks:

            - df should be raw data that comes before all the preprocessing steps
            - df can contain more columns than the features of the model such as the actual ground truth variable, sample_id, metadata, etc.
        name (Optional[str]):
            A string representing the name of the dataset (default None).
        target (Optional[str]):
            the column name in df corresponding to the actual target variable (ground truth).
        cat_columns (Optional[List[str]]):
            A list of strings representing the names of categorical columns (default None).
        infer_column_types (Optional[bool]):
            A boolean indicating whether to infer column types automatically (default False).
        column_types (Optional[Dict[str, str]]):
            A dictionary of column names and their types (numeric, category or text) for all columns of df.

    Returns:
        Dataset:
            A Giskard Dataset object that wraps the input Pandas DataFrame.

    Notes:

        - If `column_types` are provided, they are used to set the column types for the Dataset.

        - If `cat_columns` are provided, it checks if they are all part of the dataset columns. If yes, it uses
          `extract_column_types` method to extract the categorical columns and set their types accordingly.

        - If `infer_column_types` is True, it uses the `infer_column_types` method to infer column types for the Dataset.

        - If none of the above arguments are provided, it uses the `infer_column_types` method to infer column types
          for the Dataset, with the assumption that there are no categorical columns. It also issues a warning that
          there might be categorical columns that were not detected.
    """

    print("Your 'pandas.DataFrame' dataset is successfully wrapped by Giskard's 'Dataset' wrapper class.")
    return Dataset(dataset, name, target, cat_columns, column_types)
