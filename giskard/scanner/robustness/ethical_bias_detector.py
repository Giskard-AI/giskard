from typing import Sequence

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..decorators import detector
from ..issues import Ethical
from .base_detector import BaseTextPerturbationDetector
from .text_transformations import TextTransformation


@detector(
    name="ethical_bias",
    tags=["ethical_bias", "robustness", "classification", "regression"],
)
class EthicalBiasDetector(BaseTextPerturbationDetector):
    """Detects ethical bias in a model by applying text perturbations to the input data.

    By default, we perform specific metamorphic testing aimed at detecting bias in the model predictions based on
    transformation of gender, nationality, or religious terms in the textual features.

    As an example, for a sentiment analysis model we will transform a sentence like "She is such a talented singer"
    into "He is such a talented singer" and check if the model prediction changes. If it does systematically, it
    means that the model has some form of gender bias.
    """

    _issue_group = Ethical
    _taxonomy = ["avid-effect:ethics:E0101", "avid-effect:performance:P0201"]

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            TextGenderTransformation,
            TextNationalityTransformation,
            TextReligionTransformation,
        )

        return [
            TextGenderTransformation,
            TextReligionTransformation,
            TextNationalityTransformation,
        ]
