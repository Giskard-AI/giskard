from typing import Sequence

from ...datasets.base import Dataset
from ...llm.issues import PROMPT_INJECTION_ISSUE
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue
from .business_detector import LLMBusinessDetector


@detector(name="llm_prompt_injection", tags=["llm_prompt_injection", "llm", "generative", "text_generation"])
class LLMPromptInjectionDetector(LLMBusinessDetector):
    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # I keep for now the legacy behaviour
        return self._run_category_detections(PROMPT_INJECTION_ISSUE, model)
