import functools

import pandas as pd
import pydantic
from packaging import version

# See https://linear.app/giskard/issue/GSK-1745/upgrade-pydantic-to-20
IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")

if IS_PYDANTIC_V2:
    from pydantic import validate_call as validate_arguments
else:
    from pydantic import validate_arguments


def configured_validate_arguments(func):
    """
    Decorator to enforce a function args to be compatible with their type hints.
    :return: A wrapper function decorated by pydantic validate_arguments configured to allow arbitrary types check.
    """
    # https://docs.pydantic.dev/2.3/usage/validation_decorator/
    # Actually, this is more than just validation
    # If you check https://docs.pydantic.dev/latest/usage/validation_decorator/#coercion-and-strictness,
    # this explains it will try to convert/coerce type to the type hinting
    # So a string will be "coerced" to an enum element, and so on

    # Add validation wrapper
    validated_func = validate_arguments(func, config={"arbitrary_types_allowed": True})
    # Call wraps, to update name, docs, ...
    validated_func = functools.wraps(func)(validated_func)
    return validated_func


def validate_is_pandasdataframe(df):
    assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"


class ConfiguredBaseModel(pydantic.BaseModel):
    class Config:
        extra = "forbid"
        # allow_inf_nan = False Disable since some metrics can return NaN
        # May be nice to use once we drop v1 support : # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.strict
