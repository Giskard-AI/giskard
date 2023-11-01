from typing import Optional

import numbers
from enum import Enum
from functools import wraps

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset


class Direction(int, Enum):
    Invariant = 0
    Increasing = 1
    Decreasing = -1


def validate_classification_label(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        reference_slice = kwargs.get("reference_dataset", None)
        actual_slice = kwargs.get("dataset", None)
        model = kwargs.get("model", None)
        classification_label = kwargs.get("classification_label", None)
        target = getattr(reference_slice, "target", getattr(actual_slice, "target", None))

        # Try to automatically cast `classification_label` to the right type
        if (
            classification_label is not None
            and model is not None
            and isinstance(model.meta.classification_labels[0], numbers.Number)
        ):
            try:
                classification_label = int(classification_label)
                kwargs["classification_label"] = classification_label
            except ValueError:
                pass

        # Validate the label
        if target and classification_label and model:
            assert classification_label != target, (
                'By "classification_label", we refer to one of the values: '
                f'{model.meta.classification_labels} and not the target: "{target}". '
                "Please re-assign this argument."
            )

        assert (
            model.meta.model_type != SupportedModelTypes.CLASSIFICATION
            or classification_label in model.meta.classification_labels
        ), f'"{classification_label}" is not part of model labels: {model.meta.classification_labels}'
        return func(*args, **kwargs)

    return wrapper


def check_slice_not_empty(sliced_dataset: Dataset, dataset_name: Optional[str] = "", test_name: Optional[str] = ""):
    if sliced_dataset.df.empty:
        test_name = " in " + test_name
        raise ValueError("The sliced " + dataset_name + test_name + " is empty.")
