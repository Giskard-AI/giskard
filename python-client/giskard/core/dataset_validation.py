from pandas.core.dtypes.common import is_string_dtype, is_numeric_dtype
import pandas as pd
from giskard.client.python_utils import warning
from giskard.core.core import SupportedColumnTypes
from giskard.datasets.base import Dataset


def validate_target(ds: Dataset):
    if ds.target is not None:
        if ds.target not in ds.df.keys():
            raise ValueError(
                f"Invalid target parameter:"
                f" '{ds.target}' column is not present in the dataset with columns: {list(ds.df.keys())}"
            )


def validate_column_types(ds: Dataset):
    """
    Verifies that declared column_types are correct with regard to SupportedColumnTypes
    :param ds: Dataset to be validated
    """
    if ds.column_types and isinstance(ds.column_types, dict):
        if not set(ds.column_types.values()).issubset(
                set(column_type.value for column_type in SupportedColumnTypes)
        ):
            raise ValueError(
                f"Invalid column_types parameter: {ds.column_types}"
                + f"Please choose types among {[column_type.value for column_type in SupportedColumnTypes]}."
            )
    else:
        raise ValueError(f"Invalid column_types parameter: {ds.column_types}. Please specify non-empty dictionary.")

    columns_with_types = set(ds.column_types.keys())

    df = ds.df

    if ds.target in ds.df.columns:
        df = ds.df.drop(ds.target, axis=1)

    df_columns = set(df.columns)
    columns_with_types.discard(ds.target)

    if not columns_with_types.issubset(df_columns):
        missing_columns = columns_with_types - df_columns
        raise ValueError(f"Missing columns in dataframe according to column_types: {missing_columns}")
    elif not df_columns.issubset(columns_with_types):
        missing_columns = df_columns - columns_with_types
        if missing_columns:
            raise ValueError(
                f"Invalid column_types parameter: Please declare the type for " f"{missing_columns} columns"
            )


def validate_numeric_columns(ds: Dataset):
    for col, col_type in ds.column_types.items():
        if col == ds.target:
            continue
        if col_type == SupportedColumnTypes.NUMERIC.value:
            try:
                pd.to_numeric(ds.df[col])
            except ValueError:
                warning(
                    f"You declared your column '{col}' as 'numeric' but it contains non-numeric values. "
                    f"Please check if you declared the type of '{col}' correctly in 'column_types'.")


def validate_column_categorization(ds: Dataset):
    nuniques = ds.df.nunique()

    for column in ds.df.columns:
        if column == ds.target:
            continue
        # if a user provided possibly wrong information in column_types or cat_columns about cat columns
        if nuniques[column] <= ds.category_threshold and (
                ds.column_types[column] == SupportedColumnTypes.NUMERIC.value
                or ds.column_types[column] == SupportedColumnTypes.TEXT.value
        ):
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}' but has {nuniques[column]} "
                f"(<= category_threshold={ds.category_threshold}) distinct values. Are "
                f"you sure it is not a 'category' feature?"
            )
        # if a user provided possibly wrong information in column_types or cat_columns about cat columns
        elif nuniques[column] > ds.category_threshold and \
                ds.column_types[column] == SupportedColumnTypes.CATEGORY.value:
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}' but has {nuniques[column]} "
                f"(> category_threshold={ds.category_threshold}) distinct values. Are "
                f"you sure it is a 'category' feature?"
            )
        # if a user provided possibly wrong information in column_types about text columns
        elif (
                is_string_dtype(ds.df[column])
                and ds.column_types[column] == SupportedColumnTypes.NUMERIC.value
        ):
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}'. Are "
                f"you sure it is not a 'text' feature?"
            )
        # if a user provided possibly wrong information in column_types about numeric columns
        elif (
                is_numeric_dtype(ds.df[column])
                and ds.column_types[column] == SupportedColumnTypes.TEXT.value
        ):
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}'. Are "
                f"you sure it is not a 'numeric' feature?"
            )
