from typing import Dict, Sequence

from ...models.base.model import BaseModel
from ..client.base import ChatMessage
from .base import _BaseLLMEvaluator

SYS_PROMPT = """Your role is to test AI agents. Your task consists in assessing whether an Agent correctly answered a question.

The user will provide a description of the agent, the question, the agent answer and the reference (true) answer. You must tell if the Agent correctly answered the question, comparing it to the reference. If the Agent answer is correct, you will output a JSON object with "eval_passed" equal true, like this:
{"eval_passed" : true}
If the Agent answer is wrong, you will return "eval_passed" equal false and provide a reason:
{"eval_passed": false, "reason": "The agent stated that X but should have said Y"}
"""

PROMPT_TEMPLATE = """
### AGENT DESCRIPTION
{description}

### QUESTION
{question}

### AGENT ANSWER
{answer}

### REFERENCE ANSWER
{reference_answer}
"""

EX_USER_PROMPT = PROMPT_TEMPLATE.format(
    description="A chatbot for an ecommerce website, helping users to track their orders and solve issues",
    question="Which countries do you ship to?",
    answer="We ship our products across all United States.",
    reference_answer="We ship our products to the United States, Canada, and Mexico.",
)


EX_ASSISTANT_PROMPT = """{"eval_passed": false, "reason": "The agent stated that they ship to United States, but should have included Canada and Mexico."}"""


class CorrectnessEvaluator(_BaseLLMEvaluator):
    """Assess the correctness of a model answers given questions and associated reference answers."""

    def __init__(self, answer_col="reference_answer", *args, **kwargs):
        self._answer_col = answer_col
        super().__init__(*args, **kwargs)

    def _format_messages(self, model: BaseModel, conversation: Sequence[Dict], meta: Dict) -> Sequence[ChatMessage]:
        if len(conversation) < 2:
            raise ValueError("Conversation must contain at least two messages: the question and the answer.")
        try:
            reference_answer = meta[self._answer_col]
        except KeyError as err:
            raise ValueError(f"Could not find reference answer column (`{self._answer_col}`) in metadata.") from err

        prompt = PROMPT_TEMPLATE.format(
            description=model.description,
            question=conversation[-2]["content"],
            answer=conversation[-1]["content"],
            reference_answer=reference_answer,
        )

        return [
            ChatMessage(role="system", content=SYS_PROMPT),
            ChatMessage(role="user", content=EX_USER_PROMPT),
            ChatMessage(role="assistant", content=EX_ASSISTANT_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]
