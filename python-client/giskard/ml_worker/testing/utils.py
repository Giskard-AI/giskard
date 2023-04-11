import pandas as pd

from giskard.ml_worker.utils.logging import timer
from enum import Enum


class Direction(Enum):
    Invariant = 0
    Increasing = 1
    Decreasing = -1


@timer("Perturb data")
def apply_perturbation_inplace(df: pd.DataFrame, perturbation_dict):
    modified_rows = []
    i = 0
    for idx, r in df.iterrows():
        added = False
        for pert_col, pert_func in perturbation_dict.items():
            original_value = r[pert_col]
            new_value = pert_func(r)
            if original_value != new_value and not added:
                added = True
                modified_rows.append(i)
                df.loc[idx, pert_col] = new_value
        i += 1
    return modified_rows
