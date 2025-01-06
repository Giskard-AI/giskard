from typing import Sequence

from ..decorators import detector
from .base_detector import BaseNumericalPerturbationDetector
from .numerical_transformations import NumericalTransformation


class BoundClassWrapper:
    def __init__(self, cls, **bound_kwargs):
        self.cls = cls
        self.bound_kwargs = bound_kwargs

    def __call__(self, *args, **kwargs):
        return self.cls(*args, **self.bound_kwargs, **kwargs)

    def __getattr__(self, attr):
        # Forward attribute access to the wrapped class
        return getattr(self.cls, attr)


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

    def _get_default_transformations(self) -> Sequence[NumericalTransformation]:
        from .numerical_transformations import AddGaussianNoise, MultiplyByFactor

        return [
            BoundClassWrapper(MultiplyByFactor, factor=1.01),
            BoundClassWrapper(MultiplyByFactor, factor=0.99),
            BoundClassWrapper(AddGaussianNoise, mean=0, std=0.01),
        ]
