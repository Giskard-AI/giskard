import pandas as pd
from inspect import signature


def configured_validate_arguments(func):
    """
    Decorator to enforce a function args to be compatible with their type hints.
    :return: A wrapper function decorated by pydantic validate_arguments configured to allow arbitrary types check.
    """

    def wrapper(*args, **kwargs):
        sign = signature(func).parameters
        wrong_args = {}
        for i, arg in enumerate(args):
            param = list(sign.values())[i]
            if not isinstance(arg, param.annotation) and not param.annotation == param.empty:
                wrong_args[arg] = (type(arg), param.annotation)
        for k_key, k_val in kwargs.items():
            param = sign[k_key]
            if not isinstance(k_val, param.annotation) and not param.annotation == param.empty:
                wrong_args[k_key] = (type(k_val), param.annotation)

        msg = [f"{arg} is of type: {types[0]} but should have been of type: {types[1]}" for arg, types in
               wrong_args.items()]
        raise TypeError("\n".join(msg))

    return wrapper


def validate_is_pandasdataframe(df):
    assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"
