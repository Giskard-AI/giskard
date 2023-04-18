from pandas.core.dtypes.common import is_string_dtype, is_numeric_dtype

from giskard.client.python_utils import warning
from giskard.core.core import SupportedColumnTypes
from giskard.core.validation import validate_is_pandasdataframe, validate_target
from giskard.datasets.base import Dataset, Nuniques


def validate_dataset(dataset: Dataset):
    df = dataset.df
    validate_is_pandasdataframe(df)
    if dataset.target is not None:
        validate_target(dataset.target, df.keys())

    validate_column_types(dataset)
    validate_column_categorization(dataset)
    validate_column_types_vs_dtypes(dataset)


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


def validate_column_categorization(ds: Dataset):
    nuniques = ds.df.nunique()

    for column in ds.df.columns:
        if column == ds.target:
            continue
        if nuniques[column] <= Nuniques.CATEGORY.value and (
                ds.column_types[column] == SupportedColumnTypes.NUMERIC.value
                or ds.column_types[column] == SupportedColumnTypes.TEXT.value
        ):
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}' but has {nuniques[column]} "
                f"(<= Nuniques.CATEGORY.value={Nuniques.CATEGORY.value}) distinct values. Are "
                f"you sure it is not a 'category' feature?"
            )
        elif (
                nuniques[column] > Nuniques.TEXT.value
                and is_string_dtype(ds.df[column])
                and (
                        ds.column_types[column] == SupportedColumnTypes.CATEGORY.value
                        or ds.column_types[column] == SupportedColumnTypes.NUMERIC.value
                )
        ):
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}' but has {nuniques[column]} "
                f"(> Nuniques.TEXT.value={Nuniques.TEXT.value}) distinct values. Are "
                f"you sure it is not a 'text' feature?"
            )
        elif (
                nuniques[column] > Nuniques.NUMERIC.value
                and is_numeric_dtype(ds.df[column])
                and (
                        ds.column_types[column] == SupportedColumnTypes.CATEGORY.value
                        or ds.column_types[column] == SupportedColumnTypes.TEXT.value
                )
        ):
            warning(
                f"Feature '{column}' is declared as '{ds.column_types[column]}' but has {nuniques[column]} "
                f"(> Nuniques.NUMERIC.value={Nuniques.NUMERIC.value}) distinct values. Are "
                f"you sure it is not a 'numeric' feature?"
            )
