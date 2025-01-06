# giskard/scanner/robustness/numerical_perturbation_detector.py
from typing import Sequence

import pandas as pd

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..decorators import detector
from .base_numerical_detector import BaseNumericalPerturbationDetector
from .numerical_transformations import AddGaussianNoise, MultiplyByFactor, NumericalTransformation


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

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[NumericalTransformation]:
        numerical_columns = [col for col in dataset.df.columns if pd.api.types.is_numeric_dtype(dataset.df[col])]
        transformations = []
        for column in numerical_columns:
            transformations.append(MultiplyByFactor(column=column, factor=1.01))
            transformations.append(MultiplyByFactor(column=column, factor=0.99))
            transformations.append(AddGaussianNoise(column=column, mean=0, std=0.01))
        return transformations
