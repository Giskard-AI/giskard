import pandas as pd
from pydantic import validate_arguments
import functools


def validate_args(func):
    """
    Decorator to enforce a function args to be compatible with their type hints.
    :return: A wrapper function decorated by pydantic validate_arguments configured to allow arbitrary types check.
    """

    def configured_decorator(some_func):
        @validate_arguments(config=dict(arbitrary_types_allowed=True))
        @functools.wraps(some_func)  # copies the name, docstring, etc. to the wrapper function
        def wrapper(*args, **kwargs):
            return some_func(*args, **kwargs)

        return wrapper

    return configured_decorator(func)


def validate_target(target, dataframe_keys):
    if target not in dataframe_keys:
        raise ValueError(
            f"Invalid target parameter:"
            f" {target} column is not present in the dataset with columns: {dataframe_keys}"
        )


def validate_is_pandasdataframe(df):
    assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"
