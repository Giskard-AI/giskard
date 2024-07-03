from typing import Hashable

import pandas as pd

from giskard.client.python_utils import warning
from giskard.core.core import SupportedColumnTypes
from giskard.datasets import low_stat_threshold
from giskard.datasets.base import Dataset


def validate_dataset(ds: Dataset):
    validate_dtypes(ds)
    validate_target_exists(ds)
    validate_optional_target(ds)


def validate_optional_target(ds: Dataset):
    if not ds.is_target_given:
        warning(
            "You did not provide the optional argument 'target'. "
            "'target' is the column name in df corresponding to the actual target variable (ground truth)."
        )


def validate_target_exists(ds: Dataset):
    if ds.target is not None and ds.target not in ds.columns:
        raise ValueError(
            "Invalid target parameter:"
            f" '{ds.target}' column is not present in the dataset with columns: {list(ds.columns)}"
        )


def validate_dtypes(ds: Dataset):
    _check_hashability(ds.df)
    _check_mixed_dtypes(ds.df)


def _check_hashability(df):
    """This is a static method that checks if a given pandas DataFrame is hashable or not.

    It checks if all the columns containing object types in the input DataFrame are hashable or not.
    If any column is not hashable, it raises a TypeError indicating which columns are not hashable.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be checked for hashability.

    Raises
    ------
    TypeError
        If any column containing object types in the input DataFrame is not hashable.
    """
    if len(df) == 0:
        # Empty df are always hashable
        return

    df_objects = df.select_dtypes(include="object")
    non_hashable_cols = []
    for col in df_objects.columns:
        if not isinstance(df[col].iat[0], Hashable):
            non_hashable_cols.append(col)

    if non_hashable_cols:
        raise TypeError(
            f"The following columns in your df: {non_hashable_cols} are not hashable. "
            f"We currently support only hashable column types such as int, bool, str, tuple and not list or dict."
        )


def _check_mixed_dtypes(df):
    mixed_dtypes = ["mixed", "mixed-integer"]
    mixed_cols = [col for col in df.columns if pd.api.types.infer_dtype(df[col], skipna=True) in mixed_dtypes]

    if len(mixed_cols):
        raise TypeError(
            f"The following columns have mixed data types: {', '.join(mixed_cols)}. "
            "Please make sure that values in each column are of same data type (except NaN)."
        )


def validate_column_types(ds: Dataset):
    """Verifies that declared column_types are correct with regard to SupportedColumnTypes

    Parameters
    ----------
    ds : Dataset
        Dataset to be validated

    """
    if ds.column_types and isinstance(ds.column_types, dict):
        if not set(ds.column_types.values()).issubset(set(column_type.value for column_type in SupportedColumnTypes)):
            raise ValueError(
                f"Invalid column_types parameter: {ds.column_types}"
                + f"Please choose types among {[column_type.value for column_type in SupportedColumnTypes]}."
            )
    else:
        raise ValueError(f"Invalid column_types parameter: {ds.column_types}. Please specify non-empty dictionary.")

    df_columns_set = set(ds.columns)
    df_columns_set.discard(ds.target)
    column_types_set = set(ds.column_types.keys())
    column_types_set.discard(ds.target)

    if column_types_set < df_columns_set:
        missing_columns = df_columns_set - column_types_set
        raise ValueError(
            f"The following keys {list(missing_columns)} are missing from 'column_types'. "
            "Please make sure that the column names in `column_types` covers all the existing "
            "columns in your dataset."
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
                    f"Please check if you declared the type of '{col}' correctly in 'column_types'."
                )


def validate_column_categorization(ds: Dataset):
    if len(ds.df) <= low_stat_threshold:
        return

    nuniques = ds.df.nunique()

    for column in ds.columns:
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
                "you sure it is not a 'category' feature?"
            )
        # TODO: A bit noisy with a conservative category_threshold, decide on whether to include it or not.
        # if a user provided possibly wrong information in column_types or cat_columns about cat columns
        # elif nuniques[column] > ds.category_threshold and \
        #         ds.column_types[column] == SupportedColumnTypes.CATEGORY.value:
        #     warning(
        #         f"Feature '{column}' is declared as '{ds.column_types[column]}' but has {nuniques[column]} "
        #         f"(> category_threshold={ds.category_threshold}) distinct values. Are "
        #         f"you sure it is a 'category' feature?"
        #     )
        # if a user provided possibly wrong information in column_types about text columns
        else:
            if ds.column_types[column] == SupportedColumnTypes.TEXT.value:
                try:
                    pd.to_numeric(ds.df[column])
                    warning(
                        f"Feature '{column}' is declared as '{ds.column_types[column]}'. Are "
                        "you sure it is not a 'numeric' feature?"
                    )
                except ValueError:
                    pass
            elif ds.column_types[column] == SupportedColumnTypes.NUMERIC.value:
                try:
                    pd.to_numeric(ds.df[column])
                except ValueError:
                    warning(
                        f"Feature '{column}' is declared as '{ds.column_types[column]}'. Are "
                        "you sure it is not a 'text' feature?"
                    )
