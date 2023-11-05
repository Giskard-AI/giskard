from typing import Sequence

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.client import get_default_client
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue, IssueLevel, Robustness
from .base import RequirementBasedDetector

BREAKER_PROMPT = """Based on the following model description, does this AI model is performing a text reformulation or summarization task? Answer Y or N."""


FAITHFULNESS_ISSUE_DESCRIPTION = """Issue category: Faithfulness and adherence to the instructions
Issue category description: This category focuses on ensuring that the model output is consistent with the requirements requested in the model description and that if the model is performing reformulation or summarization of an input text, the output is faithful and reliable to the input text based on the model description.

Here are some examples of requirements relative to the issue category above, but which are not necessarily relevant for the specific model you are testing:
- The model should maintain a professional tone
- When summarizing a text, the model should not add information that was not present in the input text
- If the model is performing summarization, it should not never omit key information that was present in the input text"""


@detector("llm_faithfulness", tags=["faithfulness", "llm", "text_generation"])
class LLMFaithfulnessDetector(RequirementBasedDetector):
    _issue_group = Robustness
    _issue_level = IssueLevel.MAJOR

    def get_issue_description(self) -> str:
        return FAITHFULNESS_ISSUE_DESCRIPTION

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # Let’s check whether the model is performing reformulation/summarization.
        llm_client = get_default_client()
        out = llm_client.complete(
            [
                {"role": "system", "content": BREAKER_PROMPT},
                {"role": "user", "content": "Model description: " + model.meta.description},
            ],
            temperature=0.1,
            max_tokens=1,
            caller_id=self.__class__.__name__,
        )

        if out.message.strip().upper() != "Y":
            logger.warning(
                f"{self.__class__.__name__}: Skipping faithfulness checks because the model is performing a different task."
            )
            return []

        return super().run(model, dataset)
