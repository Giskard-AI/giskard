from typing import Sequence

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..decorators import detector
from .base_detector import BaseTextPerturbationDetector
from .text_transformations import TextTransformation


@detector(
    name="text_perturbation",
    tags=[
        "text_perturbation",
        "robustness",
        "classification",
        "regression",
    ],
)
class TextPerturbationDetector(BaseTextPerturbationDetector):
    """Detects robustness problems in a model by applying text perturbations to the textual features.

    This detector will check invariance of model predictions when the formatting of textual features is altered,
    e.g. transforming to uppercase, lowercase, or title case, or by introducing typos.
    """

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            TextAccentRemovalTransformation,
            TextLowercase,
            TextNumberToWordTransformation,
            TextPunctuationRemovalTransformation,
            TextTitleCase,
            TextTypoTransformation,
            TextUppercase,
        )

        return [
            TextUppercase,
            TextLowercase,
            TextTitleCase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
            TextNumberToWordTransformation,
            TextAccentRemovalTransformation,
        ]
