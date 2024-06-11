from typing import Optional

from ...llm.client import ChatMessage, LLMClient, get_default_client
from ...llm.errors import LLMGenerationError
from ..base import AgentAnswer
from ..question_generators.utils import parse_json_output
from .base import Metric

CORRECTNESS_EVALUATION_SYSTEM_PROMPT = """Your role is to test AI agents. Your task consists in assessing whether a agent output correctly answers a question. 
You are provided with the ground truth answer to the question. Your task is then to evaluate if the agent answer is close to the ground thruth answer. 

You are auditing the following agent:
{agent_description}

Think step by step and consider the agent output in its entirety. Remember: you need to have a strong and sound reason to support your evaluation.
If the agent answer is correct, return True. If the agent answer is incorrect, return False along with the reason.
You must output a single JSON object with keys 'correctness' and 'correctness_reason'. Make sure you return a valid JSON object.

The question that was asked to the agent, its output, and the expected ground truth answer will be delimited with XML tags.
"""

CORRECTNESS_INPUT_TEMPLATE = """<question>
{question}
</question>

<agent_answer>
{agent_answer}
</agent_answer>

<ground_truth>
{ground_truth}
</ground_truth>
"""


CORRECTNESS_TRUE_EXAMPLE_INPUT = CORRECTNESS_INPUT_TEMPLATE.format(
    question="What is the capital of France?", agent_answer="The capital of France is Paris.", ground_truth="Paris."
)

CORRECTNESS_TRUE_EXAMPLE_OUTPUT = """{"correctness": true, "correctness_reason": ""}"""

CORRECTNESS_FALSE_EXAMPLE_INPUT = CORRECTNESS_INPUT_TEMPLATE.format(
    question="What is the capital of Denmark?",
    agent_answer="The capital of Denmark is Paris.",
    ground_truth="Copenhagen.",
)

CORRECTNESS_FALSE_EXAMPLE_OUTPUT = (
    """{"correctness": false, "correctness_reason": "The capital of Denmark is Copenhagen, not Paris."}"""
)


class CorrectnessMetric(Metric):
    def __init__(self, name: str, llm_client: LLMClient = None, agent_description: Optional[str] = None):
        self.name = name
        self._llm_client = llm_client
        self.agent_description = agent_description or "This agent is a chatbot that answers question from users."

    def __call__(self, question_sample: dict, answer: AgentAnswer) -> dict:
        """
        Compute the correctness between the agent answer and the reference answer from QATestset.

        Parameters
        ----------
        question_sample : dict
            A question sample from a QATestset.
        answer : ModelOutput
            The answer of the agent on the question.

        Returns
        -------
        dict
            The result of the correctness evaluation. It contains the keys 'correctness' and 'correctness_reason'.
        """
        llm_client = self._llm_client or get_default_client()
        try:
            out = llm_client.complete(
                messages=[
                    ChatMessage(
                        role="system",
                        content=CORRECTNESS_EVALUATION_SYSTEM_PROMPT.format(agent_description=self.agent_description),
                    ),
                    ChatMessage(role="user", content=CORRECTNESS_TRUE_EXAMPLE_INPUT),
                    ChatMessage(role="assistant", content=CORRECTNESS_TRUE_EXAMPLE_OUTPUT),
                    ChatMessage(role="user", content=CORRECTNESS_FALSE_EXAMPLE_INPUT),
                    ChatMessage(role="assistant", content=CORRECTNESS_FALSE_EXAMPLE_OUTPUT),
                    ChatMessage(
                        role="user",
                        content=CORRECTNESS_INPUT_TEMPLATE.format(
                            question=question_sample.question,
                            agent_answer=answer.message,
                            ground_truth=question_sample.reference_answer,
                        ),
                    ),
                ],
                temperature=0,
                format="json",
            )
            return parse_json_output(
                out.content,
                llm_client=llm_client,
                keys=["correctness", "correctness_reason"],
                caller_id=self.__class__.__name__,
            )

        except Exception as err:
            raise LLMGenerationError("Error while evaluating the agent") from err


correctness_metric = CorrectnessMetric(name="correctness")
