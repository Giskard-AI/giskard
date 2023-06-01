from pandas.core.dtypes.common import is_string_dtype, is_numeric_dtype

from giskard.client.python_utils import warning
from giskard.core.core import SupportedColumnMeanings
from giskard.core.validation import validate_is_pandasdataframe, validate_target
from giskard.ml_worker.core.dataset import Dataset


def validate_dataset(dataset: Dataset):
    df = dataset.df
    validate_is_pandasdataframe(df)
    if dataset.target is not None:
        validate_target(dataset.target, df.keys())

    validate_column_meanings(dataset)
    validate_column_categorization(dataset)


def validate_column_meanings(ds: Dataset):
    """
    Verifies that declared column_meanings are correct with regard to SupportedColumnMeanings
    :param ds: Dataset to be validated
    """
    if ds.column_meanings and isinstance(ds.column_meanings, dict):
        if not set(ds.column_meanings.values()).issubset(
                set(column_meaning.value for column_meaning in SupportedColumnMeanings)
        ):
            raise ValueError(
                f"Invalid column_meanings parameter: {ds.column_meanings}"
                + f"Please choose types among {[column_meaning.value for column_meaning in SupportedColumnMeanings]}."
            )
    else:
        raise ValueError(f"Invalid column_meanings parameter: {ds.column_meanings}. Please specify non-empty dictionary.")

    columns_with_types = set(ds.column_meanings.keys())

    if ds.target in ds.df.columns:
        df = ds.df.drop(ds.target, axis=1)

    df_columns = set(df.columns)
    columns_with_types.discard(ds.target)

    if not columns_with_types.issubset(df_columns):
        missing_columns = columns_with_types - df_columns
        raise ValueError(
            f"Missing columns in dataframe according to column_meanings: {missing_columns}"
        )
    elif not df_columns.issubset(columns_with_types):
        missing_columns = df_columns - columns_with_types
        if missing_columns:
            raise ValueError(
                f"Invalid column_meanings parameter: Please declare the type for "
                f"{missing_columns} columns"
            )


def validate_column_categorization(ds: Dataset):
    nuniques = ds.df.nunique()
    nuniques_category = 2
    nuniques_numeric = 100
    nuniques_text = 1000

    for column in ds.df.columns:
        if column == ds.target:
            continue
        if nuniques[column] <= nuniques_category and \
                (ds.column_meanings[column] == SupportedColumnMeanings.NUMERIC.value or
                 ds.column_meanings[column] == SupportedColumnMeanings.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{ds.column_meanings[column]}' but has {nuniques[column]} "
                f"(<= nuniques_category={nuniques_category}) distinct values. Are "
                f"you sure it is not a 'category' feature?"
            )
        elif nuniques[column] > nuniques_text and is_string_dtype(ds.df[column]) and \
                (ds.column_meanings[column] == SupportedColumnMeanings.CATEGORY.value or
                 ds.column_meanings[column] == SupportedColumnMeanings.NUMERIC.value):
            warning(
                f"Feature '{column}' is declared as '{ds.column_meanings[column]}' but has {nuniques[column]} "
                f"(> nuniques_text={nuniques_text}) distinct values. Are "
                f"you sure it is not a 'text' feature?"
            )
        elif nuniques[column] > nuniques_numeric and is_numeric_dtype(ds.df[column]) and \
                (ds.column_meanings[column] == SupportedColumnMeanings.CATEGORY.value or
                 ds.column_meanings[column] == SupportedColumnMeanings.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{ds.column_meanings[column]}' but has {nuniques[column]} "
                f"(> nuniques_numeric={nuniques_numeric}) distinct values. Are "
                f"you sure it is not a 'numeric' feature?"
            )
