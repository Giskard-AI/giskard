from typing import Sequence

from .base_detector import BaseTextPerturbationDetector
from .text_transformations import TextTransformation
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..decorators import detector


@detector(
    name="text_perturbation",
    tags=[
        "text_perturbation",
        "robustness",
        "nlp",
        "classification",
        "regression",
        "generative",
        "text_generation",
        "llm",
    ],
)
class TextPerturbationDetector(BaseTextPerturbationDetector):
    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            TextUppercase,
            TextLowercase,
            TextTitleCase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
        )

        return [
            TextUppercase,
            TextLowercase,
            TextTitleCase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
        ]
