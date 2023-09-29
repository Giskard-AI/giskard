from typing import Sequence

from ...datasets.base import Dataset
from ...llm.issues.new_prompt_injection_issue import NEW_PROMPT_INJECTION_ISSUE
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue
from .business_detector import LLMBusinessDetector


@detector(name="new_llm_prompt_injection", tags=["new_llm_prompt_injection", "llm", "generative", "text_generation"])
class NewLLMPromptInjectionDetector(LLMBusinessDetector):
    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # I keep for now the legacy behaviour
        return self._run_category_detections(NEW_PROMPT_INJECTION_ISSUE, model, use_issue_examples=True)
