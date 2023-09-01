"""
Utility functions for model debugging notifications.

Classes:
- SupportedPerturbationType: Enumeration of supported perturbation types.
- TransformationInfo: Dataclass to hold perturbation info.

Functions:

- slice_bounds: Get quartile bounds values to slice Giskard dataset on a numerical feature.
- coltype_to_supported_perturbation_type: Map column type to perturbation type enum.

"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Union, Optional

import numpy as np

from giskard import Dataset


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


def slice_bounds(feature: str, value: Union[int, float], ds: Dataset) -> Optional[List[Union[int, float]]]:
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
            return [ds.df[feature].min(), q1]
        elif q1 <= value < q2:
            return [q1, q2]
        elif q2 <= value < q3:
            return [q2, q3]
        else:
            return [q3, ds.df[feature].max()]
    else:
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
