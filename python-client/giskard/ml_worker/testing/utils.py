from enum import Enum
from functools import wraps

from giskard.core.core import SupportedModelTypes


class Direction(Enum):
    Invariant = 0
    Increasing = 1
    Decreasing = -1


def validate_classification_label(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        reference_slice = kwargs.get('reference_dataset', None)
        actual_slice = kwargs.get('dataset', None)
        model = kwargs.get('model', None)
        classification_label = kwargs.get('classification_label', None)
        target = getattr(reference_slice, 'target', getattr(actual_slice, 'target', None))
        if target and classification_label and model:
            assert (classification_label != target
                    ), f'By "classification_label", we refer to one of the values: ' \
                       f'{model.meta.classification_labels} and not the target: "{target}". ' \
                       f'Please re-assign this argument.'

        assert (model.meta.model_type != SupportedModelTypes.CLASSIFICATION
                or classification_label in model.meta.classification_labels
                ), f'"{classification_label}" is not part of model labels: {model.meta.classification_labels}'
        return func(*args, **kwargs)

    return wrapper
