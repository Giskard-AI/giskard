import pandas as pd
from pydantic import validate_arguments
import functools


def configured_validate_arguments(func):
    """
    Decorator to enforce a function args to be compatible with their type hints.
    :return: A wrapper function decorated by pydantic validate_arguments configured to allow arbitrary types check.
    """
    return functools.wraps(func)(validate_arguments(config=dict(arbitrary_types_allowed=True))(func))


def validate_is_pandasdataframe(df):
    assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"
