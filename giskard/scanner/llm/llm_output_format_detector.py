from typing import Sequence

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.client import get_default_client
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
    _issue_group = OutputFormatting
    _issue_level = IssueLevel.MEDIUM

    def get_issue_description(self) -> str:
        return OUTPUT_FORMAT_ISSUE_DESCRIPTION

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # Let’s check whether the model description provides information about the output format.
        llm_client = get_default_client()
        out = llm_client.complete(
            [
                {"role": "system", "content": BREAKER_PROMPT},
                {"role": "user", "content": "Model description: " + model.meta.description},
            ],
            temperature=0.1,
            max_tokens=1,
        )

        if out.message.strip().upper() != "Y":
            logger.warning(
                f"{self.__class__.__name__}: Skipping output format checks because we could not define format requirements based on the model description."
            )
            return []

        return super().run(model, dataset)
