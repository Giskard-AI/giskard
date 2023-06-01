import pandas as pd
from functools import wraps
from giskard.core.core import SupportedModelTypes
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


def validate_classification_label(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        reference_slice = kwargs.get('reference_slice', None)
        actual_slice = kwargs.get('actual_slice', None)
        model = kwargs.get('model', None)
        classification_label = str(kwargs.get('classification_label', None))
        target = getattr(reference_slice, 'target', getattr(actual_slice, 'target', None))
        if target and classification_label and model:
            assert (classification_label != target
                    ), f'By "classification_label", we refer to one of the values: ' \
                       f'[{",".join(model.meta.classification_labels)}] and not the target: "{target}". ' \
                       f'Please re-assign this argument.'

        assert (model.meta.model_type != SupportedModelTypes.CLASSIFICATION
                or classification_label in model.meta.classification_labels
                ), f'"{classification_label}" is not part of model labels: {",".join(model.meta.classification_labels)}'
        return func(*args, **kwargs)

    return wrapper
