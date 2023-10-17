from typing import Dict, Optional, List

import pandas as pd
import logging

from giskard.core.validation import configured_validate_arguments
from giskard.datasets.base import Dataset

from .metadata import MetadataProviderRegistry
from .metadata.text_metadata_provider import TextMetadataProvider

# Register metadata providers on import
MetadataProviderRegistry.register(TextMetadataProvider())

# threshold below which we don't perform:
# - validate_column_categorization
low_stat_threshold = 100

logger = logging.getLogger(__name__)


@configured_validate_arguments
def wrap_dataset(
    df: pd.DataFrame,
    name: Optional[str] = None,
    target: Optional[str] = None,
    cat_columns: Optional[List[str]] = None,
    column_types: Optional[Dict[str, str]] = None,
):
    """
    A function that wraps a Pandas DataFrame into a Giskard Dataset object, with optional validation of input arguments.

    Args:
        df (pd.DataFrame):
            A Pandas dataframe that contains some data examples that might interest you to inspect (test set, train set,
            production data). Some important remarks:

            - df should be the raw data that comes before all the preprocessing steps
            - df can contain more columns than the features of the model such as the actual ground truth variable,
            sample_id, metadata, etc.
        name (Optional[str]):
            A string representing the name of the dataset (default None).
        target (Optional[str]):
            The column name in df corresponding to the actual target variable (ground truth).
        cat_columns (Optional[List[str]]):
            A list of strings representing the names of categorical columns (default None). If not provided,
            the categorical columns will be automatically inferred.
        column_types (Optional[Dict[str, str]]):
            A dictionary of column names and their types (numeric, category or text) for all columns of df. If not provided,
            the categorical columns will be automatically inferred.

    Returns:
        Dataset:
            A Giskard Dataset object that wraps the input Pandas DataFrame.

    Notes:

        - If `column_types` are provided, they are used to set the column types for the Dataset.

        - If `cat_columns` are provided, it checks if they are all part of the dataset columns and uses them as
          categorical columns.

        - If none of the above arguments are provided, the column types are inferred automatically.
    """

    logger.info("Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.")
    return Dataset(df, name, target, cat_columns, column_types)
