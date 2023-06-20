from typing import Sequence

from .issues import EthicalIssue

from .base_detector import BaseTextPerturbationDetector
from .text_transformations import TextTransformation
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..decorators import detector


@detector(
    name="ethical_bias",
    tags=["ethical_bias", "robustness", "nlp", "classification", "regression", "generative", "text_generation", "llm"],
)
class EthicalBiasDetector(BaseTextPerturbationDetector):
    _issue_cls = EthicalIssue

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            TextGenderTransformation,
            TextReligionTransformation,
            TextNationalityTransformation,
        )

        return [
            TextGenderTransformation,
            TextReligionTransformation,
            TextNationalityTransformation,
        ]
