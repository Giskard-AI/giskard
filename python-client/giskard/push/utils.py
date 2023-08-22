from dataclasses import dataclass
import numpy as np
from enum import Enum


class SupportedPerturbationType(Enum):
    NUMERIC = "numeric"
    TEXT = "text"


def slice_bounds(feature, value, ds):
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
    value_perturbed: list
    transformation_functions: list
    transformation_functions_params: list


def coltype_to_supported_perturbation_type(coltype: str) -> SupportedPerturbationType:
    if coltype == "numeric":
        return SupportedPerturbationType.NUMERIC
    elif coltype == "text":
        return SupportedPerturbationType.TEXT
