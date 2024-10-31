from typing import Sequence

import numpy as np

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..decorators import detector
from .base_numerical_detector import BaseNumericalPerturbationDetector


@detector(
    name="numerical_perturbation",
    tags=[
        "numerical_perturbation",
        "robustness",
        "classification",
        "regression",
    ],
)
class NumericalPerturbationDetector(BaseNumericalPerturbationDetector):
    """Detects robustness problems in a model by applying numerical perturbations to the numerical features."""

    def _get_default_perturbations(self, model: BaseModel, dataset: Dataset) -> Sequence:
        return [
            lambda x: x * 1.01,
            lambda x: x * 0.99,
            lambda x: x + np.random.normal(0, 0.01, x.shape),
        ]
