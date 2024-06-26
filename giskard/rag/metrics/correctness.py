from typing import Optional

from ...llm.client import ChatMessage, LLMClient, get_default_client
from ...llm.errors import LLMGenerationError
from ..base import AgentAnswer
from ..question_generators.utils import parse_json_output
from .base import Metric


def format_conversation(conversation: list[dict]):
    return "\n\n".join([f"<{msg['role'].lower()}>{msg['content']}</{msg['role'].lower()}>" for msg in conversation])


CORRECTNESS_EVALUATION_SYSTEM_PROMPT = """Your role is to test AI assistants. Your task consists in assessing whether an Agent correctly answered a question.

The user will provide a description of the agent, a conversation between the Agent (<assistant>) and the user (<user>), the agent answer to the last question of the conversation and the reference (true) answer. You must tell if the Agent correctly answered the question, comparing it to the reference. 
Be sure to take the conversation history into account. 

If the Agent answer is correct, you will output a JSON object with "eval_passed" equal true, like this:
{"correctness" : true}
If the Agent answer is wrong, you will return "eval_passed" equal false and provide a reason:
{"correctness": false, "correctness_reason": "The agent stated that X but should have said Y"}
"""

CORRECTNESS_INPUT_TEMPLATE = """
### AGENT DESCRIPTION
{description}

### CONVERSATION
{conversation}

### AGENT ANSWER
{answer}

### REFERENCE ANSWER
{reference_answer}
"""

CORRECTNESS_TRUE_EXAMPLE_INPUT = CORRECTNESS_INPUT_TEMPLATE.format(
    description="A chatbot for an ecommerce website, helping users to track their orders and solve issues",
    conversation="<user>Which countries do you ship to?</user>",
    answer="We ship our products across all United States.",
    reference_answer="We ship our products to the United States, Canada, and Mexico.",
)

CORRECTNESS_TRUE_EXAMPLE_OUTPUT = """{"correctness": false, "correctness_reason": "The agent stated that they ship to United States, but should have included Canada and Mexico."}"""

CORRECTNESS_TRUE_EXAMPLE_INPUT_CONV = CORRECTNESS_INPUT_TEMPLATE.format(
    description="An educational chatbot for physics students, helping them with homework and explaining concepts",
    conversation="""<user>: Hello, I have some trouble understanding the Archimedes' principle.</user>

<assistant>Hi, sure I can help you with that, what do you want to know?</assistant>

<user>Where does it act?</user>""",
    answer="The Archimedes' principle acts at the center of gravity of an object.",
    reference_answer="The Archimedes' principle acts at the center of buoyancy of an object. It is the center of gravity of the displaced fluid.",
)

CORRECTNESS_TRUE_EXAMPLE_OUTPUT_CONV = """{"correctness": false, "correctness_reason": "The agent stated that the Archimedes' principle acts at the center of gravity of an object, but should have said that it acts at the center of buoyancy of the object."}"""


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
                        content=CORRECTNESS_EVALUATION_SYSTEM_PROMPT,
                    ),
                    ChatMessage(role="user", content=CORRECTNESS_TRUE_EXAMPLE_INPUT),
                    ChatMessage(role="assistant", content=CORRECTNESS_TRUE_EXAMPLE_OUTPUT),
                    ChatMessage(role="user", content=CORRECTNESS_TRUE_EXAMPLE_INPUT_CONV),
                    ChatMessage(role="assistant", content=CORRECTNESS_TRUE_EXAMPLE_OUTPUT_CONV),
                    ChatMessage(
                        role="user",
                        content=CORRECTNESS_INPUT_TEMPLATE.format(
                            conversation=format_conversation(
                                question_sample.conversation_history
                                + [{"role": "user", "content": question_sample.question}]
                            ),
                            answer=answer.message,
                            reference_answer=question_sample.reference_answer,
                            description=self.agent_description,
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
