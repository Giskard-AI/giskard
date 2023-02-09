from pandas.core.dtypes.common import is_string_dtype, is_numeric_dtype

from giskard.client.python_utils import warning
from giskard.core.core import SupportedFeatureTypes
from giskard.core.validation import validate_is_pandasdataframe, validate_target
from giskard.ml_worker.core.dataset import Dataset


def validate_dataset(dataset: Dataset):
    df = dataset.df
    validate_is_pandasdataframe(df)
    if dataset.target is not None:
        validate_target(dataset.target, df.keys())

    validate_feature_types(dataset)
    validate_column_categorization(dataset)


def validate_feature_types(ds: Dataset):
    """
    Verifies that declared feature_types are correct with regard to SupportedFeatureTypes
    :param ds: Dataset to be validated
    """
    if ds.feature_types and isinstance(ds.feature_types, dict):
        if not set(ds.feature_types.values()).issubset(
                set(feature_type.value for feature_type in SupportedFeatureTypes)
        ):
            raise ValueError(
                f"Invalid feature_types parameter: {ds.feature_types}"
                + f"Please choose types among {[feature_type.value for feature_type in SupportedFeatureTypes]}."
            )
    else:
        raise ValueError(f"Invalid feature_types parameter: {ds.feature_types}. Please specify non-empty dictionary.")

    columns_with_types = set(ds.feature_types.keys())

    df = ds.df

    if ds.target in ds.df.columns:
        df = ds.df.drop(ds.target, axis=1)

    df_columns = set(df.columns)
    columns_with_types.discard(ds.target)

    if not columns_with_types.issubset(df_columns):
        missing_columns = columns_with_types - df_columns
        raise ValueError(
            f"Missing columns in dataframe according to feature_types: {missing_columns}"
        )
    elif not df_columns.issubset(columns_with_types):
        missing_columns = df_columns - columns_with_types
        if missing_columns:
            raise ValueError(
                f"Invalid feature_types parameter: Please declare the type for "
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
                (ds.feature_types[column] == SupportedFeatureTypes.NUMERIC.value or
                 ds.feature_types[column] == SupportedFeatureTypes.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{ds.feature_types[column]}' but has {nuniques[column]} "
                f"(<= nuniques_category={nuniques_category}) distinct values. Are "
                f"you sure it is not a 'category' feature?"
            )
        elif nuniques[column] > nuniques_text and is_string_dtype(ds.df[column]) and \
                (ds.feature_types[column] == SupportedFeatureTypes.CATEGORY.value or
                 ds.feature_types[column] == SupportedFeatureTypes.NUMERIC.value):
            warning(
                f"Feature '{column}' is declared as '{ds.feature_types[column]}' but has {nuniques[column]} "
                f"(> nuniques_text={nuniques_text}) distinct values. Are "
                f"you sure it is not a 'text' feature?"
            )
        elif nuniques[column] > nuniques_numeric and is_numeric_dtype(ds.df[column]) and \
                (ds.feature_types[column] == SupportedFeatureTypes.CATEGORY.value or
                 ds.feature_types[column] == SupportedFeatureTypes.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{ds.feature_types[column]}' but has {nuniques[column]} "
                f"(> nuniques_numeric={nuniques_numeric}) distinct values. Are "
                f"you sure it is not a 'numeric' feature?"
            )
