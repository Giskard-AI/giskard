from typing import Sequence

from giskard.datasets.base import Dataset
from giskard.models.base.model import BaseModel
from giskard.scanner.robustness.feature_transformation import CategorialTransformation 

from .base_detector import BaseCategorialPertubationDetector
from ..issues import Robustness
from ..decorators import detector

@detector(
    name="swtich_all",
    tags=["switch_all", "robustness", "classification", "regression"],
)
class SwitchAllDetector(BaseCategorialPertubationDetector):
    """Detect if a pertubation of a single categorial column from the input data can pertub the model. 

    By default, we simply perform a shuffle of the data.
    
    As an example is having a breed category with values potential values: ['Labrador', 'Husky', 'Beagle', ...].
    The idea is to switch all Labrador` value to any other breed and so on.
    """

    _issue_group = Robustness
    # @TODO: find information related to the taxonomy
    _taxonomy = None 

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[CategorialTransformation]:
        from .feature_transformation import (
            CategorialShuffle
        )

        return [CategorialShuffle]