"""
utils.py

Utility functions for model debugging.

Functions:

- slice_bounds: Get value bounds to slice dataset on a feature.
- bins_count: Count bins for categorical features.  
- TransformationInfo: Dataclass to hold perturbation info.
- coltype_to_supported_perturbation_type: Map column type to perturbation type enum.

"""

from dataclasses import dataclass
import numpy as np
from enum import Enum


class SupportedPerturbationType(Enum):
    """Enumeration of supported perturbation types."""

    NUMERIC = "numeric"
    TEXT = "text"


def slice_bounds(feature, value, ds):
    """Get bounds to slice dataset based on a feature value.

    Args:
        feature (str): Feature name
        value (object): Feature value
        ds (Dataset): Dataset

    Returns:
        list: Lower and upper bounds for slice
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


def bins_count(model, dataframe):  # done at the beggining
    """Count unique values for categorical features.

    Args:
        model (BaseModel): Model
        dataframe (DataFrame): Dataframe

    Returns:
        dict: Dictionary of value counts for categorical features
    """

    df = dataframe

    columns_to_encode = [key for key in model.column_types.keys() if model.column_types[key] == "category"]
    value_counts = {}
    for column in columns_to_encode:
        nunique = df[column].nunique()
        ratio = len(df) / nunique
        counts = df[column].value_counts().to_dict()
        flag = {value: count < ratio for value, count in counts.items()}
        value_counts[column] = {"value_counts": counts, "nunique": nunique, "ratio": ratio, "flag": flag}
    return value_counts


@dataclass
class TransformationInfo:
    """Class to hold perturbation transformation information."""

    value_perturbed: list
    transformation_functions: list
    transformation_functions_params: list


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
