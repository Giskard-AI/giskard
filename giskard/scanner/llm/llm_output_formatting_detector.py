from typing import Sequence

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.client import get_default_client
from ...llm.client.base import ChatMessage
from ...models.base.model import BaseModel
from ..decorators import detector
from ..issues import Issue, IssueLevel, OutputFormatting
from .base import RequirementBasedDetector

BREAKER_PROMPT = """Based on the following model description, does this AI model require a specific format for its output?

Think step by step. For example, if the model description says that the model output should be valid HTML, you should answer Y.
If the model description says that the model output should be valid JSON format, you should answer Y.
If the model description says that the model should produce a list of 5 elements, you should answer Y.
If the model description does not provide any information about the output format, you should answer N.
If you are in doubt, you should answer N.

Answer Y or N."""


OUTPUT_FORMAT_ISSUE_DESCRIPTION = """Issue category: Output formatting
Issue category description: This category focuses on ensuring that the model output is consistent with format requirements indicated in the model description, if any. 

Here are some examples of requirements relative to the issue category above, but which are not necessarily relevant for the specific model you are testing:
- Model output should not be longer than 3 sentences
- The model output should be valid HTML
- Responses must be valid JSON format"""


@detector("llm_output_formatting", tags=["output_formatting", "llm", "text_generation"])
class LLMOutputFormattingDetector(RequirementBasedDetector):
    """Detects output formatting issues in LLM-based models.

    This detector checks that the model output is consistent with format requirements indicated in the model description, if any.
    """

    _issue_group = OutputFormatting
    _issue_level = IssueLevel.MEDIUM
    _taxonomy = ["avid-effect:performance:P0204"]

    def get_cost_estimate(self, model: BaseModel, dataset: Dataset) -> dict:
        data = super().get_cost_estimate(model, dataset)

        # Add the cost of the breaker prompt
        data["llm_calls"] += 1
        data["llm_prompt_tokens"] += 200
        data["llm_sampled_tokens"] += 1

        return data

    def get_issue_description(self) -> str:
        return OUTPUT_FORMAT_ISSUE_DESCRIPTION

    def run(self, model: BaseModel, dataset: Dataset, features=None) -> Sequence[Issue]:
        # Let’s check whether the model description provides information about the output format.
        llm_client = get_default_client()
        out = llm_client.complete(
            [
                ChatMessage(role="system", content=BREAKER_PROMPT),
                ChatMessage(role="user", content="Model description: " + model.meta.description),
            ],
            temperature=0.1,
            max_tokens=1,
            caller_id=self.__class__.__name__,
            seed=self.llm_seed,
        )

        if out.content.strip().upper() != "Y":
            logger.warning(
                f"{self.__class__.__name__}: Skipping output format checks because we could not define format requirements based on the model description."
            )
            return []

        return super().run(model, dataset, features=features)
