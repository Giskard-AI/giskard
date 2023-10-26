"""
Utility functions for model debugging notifications.

Classes:
- SupportedPerturbationType: Enumeration of supported perturbation types.
- TransformationInfo: Dataclass to hold perturbation info.

Functions:

- slice_bounds_quartile: Get quartile bounds values to slice Giskard dataset on a numerical feature.
- coltype_to_supported_perturbation_type: Map column type to perturbation type enum.

"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Union

import numpy as np

from giskard.datasets import Dataset


class SupportedPerturbationType(Enum):
    """Enumeration of supported perturbation types."""

    NUMERIC = "numeric"
    TEXT = "text"


@dataclass
class TransformationInfo:
    """Class to hold perturbation transformation information."""

    value_perturbed: list
    transformation_functions: list
    transformation_functions_params: list


def slice_bounds_quartile(feature: str, value: Union[int, float], ds: Dataset) -> Optional[Tuple[Union[int, float]]]:
    """Get quartile bounds values to slice Giskard dataset on a numerical feature.

    Args:
        feature (str): Feature name
        value (float or int): Feature value
        ds (Dataset): Dataset

    Returns:
        list: Lower and upper bounds of the slice
    """
    if ds.column_types[feature] == "numeric":
        # Find the quartile bounds for the value
        q1, q2, q3 = np.nanpercentile(ds.df[feature], [25, 50, 75])
        if value < q1:
            return (ds.df[feature].min(), q1)
        elif q1 <= value < q2:
            return (q1, q2)
        elif q2 <= value < q3:
            return (q2, q3)
        return (q3, ds.df[feature].max())
    return None


def slice_bounds_relative(
    feature: str, value: Union[int, float], ds: Dataset, window_size: float = 0.1
) -> Optional[Tuple[Union[int, float]]]:
    """Get fixed bounds values to slice Giskard dataset on a numerical feature.

    Args:
        feature (str): Feature name
        value (float or int): Feature value
        ds (Dataset): Dataset
        window_size (float): interval in percentage around the value

    Returns:
        tuple: Lower and upper bounds of the slice
    """
    if ds.column_types[feature] == "numeric":
        add_value = value * window_size / 2.0
        up = value + add_value if value > 0 else value - add_value
        low = value - add_value if value > 0 else value + add_value

        _max = ds.df[feature].max()
        _min = ds.df[feature].min()

        up = up if up <= _max else _max
        low = low if low >= _min else _min

        return (low, up)
    return None


def coltype_to_supported_perturbation_type(coltype: str) -> SupportedPerturbationType:
    """Map column type to supported perturbation type enum.

    Args:
        coltype (str): Column type

    Returns:
        SupportedPerturbationType: Perturbation type enum
    """
    if coltype == "numeric":
        return SupportedPerturbationType.NUMERIC
    elif coltype == "text":
        return SupportedPerturbationType.TEXT
