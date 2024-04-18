from typing import Sequence

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.client import get_default_client
from ...llm.client.base import ChatMessage
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue, IssueLevel, Robustness
from .base import RequirementBasedDetector

BREAKER_PROMPT = (
    "Based on the following description, does this AI agent perform a text reformulation "
    "or summarization task? Answer Y or N."
)


FAITHFULNESS_ISSUE_DESCRIPTION = (
    "Faithfulness and adherence to the instructions (the agent output is consistent with the requirements specified "
    "in the agent description and if the model is performing reformulation or summarization of an input text, the "
    "output is faithful and reliable to the input text)."
)


@detector("llm_faithfulness", tags=["faithfulness", "llm", "text_generation"])
class LLMFaithfulnessDetector(RequirementBasedDetector):
    _issue_group = Robustness
    _issue_level = IssueLevel.MAJOR

    def get_issue_description(self) -> str:
        return FAITHFULNESS_ISSUE_DESCRIPTION

    def run(self, model: BaseModel, dataset: Dataset, features=None) -> Sequence[Issue]:
        # Let’s check whether the model is performing reformulation/summarization.
        llm_client = get_default_client()
        out = llm_client.complete(
            [
                ChatMessage(role="system", content=BREAKER_PROMPT),
                ChatMessage(role="user", content="Agent description: " + model.description),
            ],
            temperature=0.1,
            max_tokens=1,
            caller_id=self.__class__.__name__,
            seed=self.llm_seed,
        )

        if out.content.strip().upper() != "Y":
            logger.warning(
                f"{self.__class__.__name__}: Skipping faithfulness checks because the model is performing a different task."
            )
            return []

        return super().run(model, dataset, features=features)
