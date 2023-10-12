from typing import Sequence

from ...datasets.base import Dataset
from ...llm.issues import DISCLOSURE_OF_SENSITIVE_INFORMATION_ISSUE
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue
from .business_detector import LLMBusinessDetector


@detector("llm_information_disclosure", tags=["information_disclosure", "llm", "generative", "text_generation"])
class LLMInformationDisclosure(LLMBusinessDetector):
    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # I keep for now the legacy behaviour
        return self._run_category_detections(DISCLOSURE_OF_SENSITIVE_INFORMATION_ISSUE, model)
