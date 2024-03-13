from typing import Optional, Sequence

import json

import pandas as pd
from tqdm.auto import tqdm

from ...llm.client.base import LLMClient, LLMMessage
from ...llm.errors import LLMGenerationError
from ..testset import QATestset
from .base import Metric

CORRECTNESS_EVALUATION_SYSTEM_PROMPT = """Your role is to test AI assistants. Your task consists in assessing whether a assistant output correctly answers a question. 
You are provided with the ground truth answer to the question. Your task is then to evaluate if the assistant answer is close to the ground thruth answer. 

You are auditing the following assistant:
{assistant_description}

Think step by step and consider the assistant output in its entirety. Remember: you need to have a strong and sound reason to support your evaluation.
If the assistant answer is correct, return True. If the assistant answer is incorrect, return False along with the reason.
You must output a single JSON object with keys 'correctness' and 'correctness_reason'. Make sure you return a valid JSON object.

The question that was asked to the assistant, its output, and the expected ground truth answer will be delimited with XML tags.
"""

CORRECTNESS_INPUT_TEMPLATE = """<question>
{question}
</question>

<assistant_answer>
{assistant_answer}
</assistant_answer>

<ground_truth>
{ground_truth}
</ground_truth>
"""


CORRECTNESS_TRUE_EXAMPLE_INPUT = CORRECTNESS_INPUT_TEMPLATE.format(
    question="What is the capital of France?", assistant_answer="The capital of France is Paris.", ground_truth="Paris."
)

CORRECTNESS_TRUE_EXAMPLE_OUTPUT = """{"correctness": true, "correctness_reason": ""}"""

CORRECTNESS_FALSE_EXAMPLE_INPUT = CORRECTNESS_INPUT_TEMPLATE.format(
    question="What is the capital of Denmark?",
    assistant_answer="The capital of Denmark is Paris.",
    ground_truth="Copenhagen.",
)

CORRECTNESS_FALSE_EXAMPLE_OUTPUT = (
    """{"correctness": false, "correctness_reason": "The capital of Denmark is Copenhagen, not Paris."}"""
)


class CorrectnessMetric(Metric):
    def __init__(self, name: str, assistant_description: Optional[str] = None):
        self.name = name
        self.assistant_description = (
            assistant_description or "This assistant is a chatbot that answers question from users."
        )

    def __call__(self, testset: QATestset, answers: Sequence[str], llm_client: LLMClient) -> dict:
        results = []
        for sample, answer in tqdm(
            zip(testset.to_pandas().reset_index().itertuples(), answers),
            desc=f"{self.name} evaluation",
            total=len(answers),
        ):
            try:
                out = llm_client.complete(
                    messages=[
                        LLMMessage(
                            role="system",
                            content=CORRECTNESS_EVALUATION_SYSTEM_PROMPT.format(
                                assistant_description=self.assistant_description
                            ),
                        ),
                        LLMMessage(role="user", content=CORRECTNESS_TRUE_EXAMPLE_INPUT),
                        LLMMessage(role="assistant", content=CORRECTNESS_TRUE_EXAMPLE_OUTPUT),
                        LLMMessage(role="user", content=CORRECTNESS_FALSE_EXAMPLE_INPUT),
                        LLMMessage(role="assistant", content=CORRECTNESS_FALSE_EXAMPLE_OUTPUT),
                        LLMMessage(
                            role="user",
                            content=CORRECTNESS_INPUT_TEMPLATE.format(
                                question=sample.question, assistant_answer=answer, ground_truth=sample.reference_answer
                            ),
                        ),
                    ],
                    temperature=0,
                )
                evaluation = json.loads(out.content, strict=False)
                evaluation["id"] = sample.id
                results.append(evaluation)
            except Exception as err:
                raise LLMGenerationError(f"Error while evaluating the assistant: {err}")

        return {"correctness": pd.DataFrame(results).set_index("id")}


correctness_metric = CorrectnessMetric(name="correctness")
