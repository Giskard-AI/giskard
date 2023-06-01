import pandas as pd
from pandas.core.dtypes.common import is_string_dtype, is_numeric_dtype

from giskard.client.python_utils import warning
from giskard.core.core import SupportedColumnType
from giskard.core.validation import validate_is_pandasdataframe, validate_target
from giskard.ml_worker.core.dataset import Dataset


def validate_dataset(dataset: Dataset):
    df = dataset.df
    validate_is_pandasdataframe(df)
    if dataset.target is not None:
        validate_target(dataset.target, df.keys())
    validate_columns_columntypes(df, dataset.column_types, dataset.target)
    validate_column_types(dataset.feature_types)
    validate_column_categorization(df, dataset.column_types)


def validate_column_types(column_types):
    if column_types and isinstance(column_types, dict):
        if not set(column_types.values()).issubset(
                set(column_type.value for column_type in SupportedColumnType)
        ):
            raise ValueError(
                f"Invalid column_types parameter: "
                + f"Please choose types among {[column_type.value for column_type in SupportedColumnType]}."
            )
    else:
        raise ValueError(
            f"Invalid column_types parameter: {column_types}. Please specify non-empty dictionary."
        )


def validate_columns_columntypes(df: pd.DataFrame, feature_types, target) -> pd.DataFrame:
    columns_with_types = set(feature_types.keys())

    if target in df.columns:
        df = df.drop(target, axis=1)

    df_columns = set(df.columns)
    columns_with_types.discard(target)

    if not columns_with_types.issubset(df_columns):
        missing_columns = columns_with_types - df_columns
        raise ValueError(
            f"Missing columns in dataframe according to column_types: {missing_columns}"
        )
    elif not df_columns.issubset(columns_with_types):
        missing_columns = df_columns - columns_with_types
        if missing_columns:
            raise ValueError(
                f"Invalid column_types parameter: Please declare the type for "
                f"{missing_columns} columns"
            )

    pandas_inferred_column_types = df.dtypes.to_dict()
    for column, dtype in pandas_inferred_column_types.items():
        if (
                feature_types.get(column) == SupportedColumnType.NUMERIC.value
                and dtype == "object"
        ):
            try:
                df[column] = df[column].astype(float)
            except Exception as e:
                raise ValueError(f"Failed to convert column '{column}' to float") from e
        return df


def validate_column_categorization(df: pd.DataFrame, feature_types):
    nuniques = df.nunique()
    nuniques_category = 2
    nuniques_numeric = 100
    nuniques_text = 1000

    for column in df.columns:
        if nuniques[column] <= nuniques_category and \
                (feature_types[column] == SupportedColumnType.NUMERIC.value or
                 feature_types[column] == SupportedColumnType.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} "
                f"(<= nuniques_category={nuniques_category}) distinct values. Are "
                f"you sure it is not a 'category' feature?"
            )
        elif nuniques[column] > nuniques_text and is_string_dtype(df[column]) and \
                (feature_types[column] == SupportedColumnType.CATEGORY.value or
                 feature_types[column] == SupportedColumnType.NUMERIC.value):
            warning(
                f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} "
                f"(> nuniques_text={nuniques_text}) distinct values. Are "
                f"you sure it is not a 'text' feature?"
            )
        elif nuniques[column] > nuniques_numeric and is_numeric_dtype(df[column]) and \
                (feature_types[column] == SupportedColumnType.CATEGORY.value or
                 feature_types[column] == SupportedColumnType.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} "
                f"(> nuniques_numeric={nuniques_numeric}) distinct values. Are "
                f"you sure it is not a 'numeric' feature?"
            )
