import pandas as pd
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

    validate_feature_types(dataset.df, dataset.feature_types, dataset.target)
    validate_column_categorization(df, dataset.feature_types)


def validate_feature_types(df, feature_types, target):
    """
    Verifies that declared feature_types are correct with regard to SupportedFeatureTypes
    :param feature_types: Map of feature name to one of the SupportedFeatureTypes values
    """
    if feature_types and isinstance(feature_types, dict):
        if not set(feature_types.values()).issubset(
                set(column_type.value for column_type in SupportedFeatureTypes)
        ):
            raise ValueError(
                f"Invalid feature_types parameter: {feature_types}"
                + f"Please choose types among {[column_type.value for column_type in SupportedFeatureTypes]}."
            )
    else:
        raise ValueError(f"Invalid feature_types parameter: {feature_types}. Please specify non-empty dictionary.")

    columns_with_types = set(feature_types.keys())

    if target in df.columns:
        df = df.drop(target, axis=1)

    df_columns = set(df.columns)
    columns_with_types.discard(target)

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


def validate_column_categorization(df: pd.DataFrame, feature_types):
    nuniques = df.nunique()
    nuniques_category = 2
    nuniques_numeric = 100
    nuniques_text = 1000

    for column in df.columns:
        if nuniques[column] <= nuniques_category and \
                (feature_types[column] == SupportedFeatureTypes.NUMERIC.value or
                 feature_types[column] == SupportedFeatureTypes.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} "
                f"(<= nuniques_category={nuniques_category}) distinct values. Are "
                f"you sure it is not a 'category' feature?"
            )
        elif nuniques[column] > nuniques_text and is_string_dtype(df[column]) and \
                (feature_types[column] == SupportedFeatureTypes.CATEGORY.value or
                 feature_types[column] == SupportedFeatureTypes.NUMERIC.value):
            warning(
                f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} "
                f"(> nuniques_text={nuniques_text}) distinct values. Are "
                f"you sure it is not a 'text' feature?"
            )
        elif nuniques[column] > nuniques_numeric and is_numeric_dtype(df[column]) and \
                (feature_types[column] == SupportedFeatureTypes.CATEGORY.value or
                 feature_types[column] == SupportedFeatureTypes.TEXT.value):
            warning(
                f"Feature '{column}' is declared as '{feature_types[column]}' but has {nuniques[column]} "
                f"(> nuniques_numeric={nuniques_numeric}) distinct values. Are "
                f"you sure it is not a 'numeric' feature?"
            )
