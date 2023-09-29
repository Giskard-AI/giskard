from typing import Sequence

from ...datasets.base import Dataset
from ...llm.issues import GENERATION_OF_HARMFUL_CONTENT_ISSUE
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue
from .business_detector import LLMBusinessDetector


@detector("llm_harmful_content", tags=["llm", "generative", "text_generation"])
class LLMHarmfulContentDetector(LLMBusinessDetector):
    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # I keep for now the legacy behaviour
        return self._run_category_detections(GENERATION_OF_HARMFUL_CONTENT_ISSUE, model)
