from typing import Sequence

from ...datasets.base import Dataset
from ...llm.issues import STEREOTYPE_AND_DISCRIMINATION_ISSUE
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue
from .business_detector import LLMBusinessDetector


@detector("llm_stereotype", tags=["llm", "generative", "text_generation"])
class LLMStereotypeDetector(LLMBusinessDetector):
    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # I keep for now the legacy behaviour
        return self._run_category_detections(STEREOTYPE_AND_DISCRIMINATION_ISSUE, model)
