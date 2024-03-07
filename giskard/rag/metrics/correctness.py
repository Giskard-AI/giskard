from typing import Optional, Sequence

import json

import pandas as pd

from ...llm.client.base import LLMClient, LLMMessage
from ...llm.errors import LLMGenerationError
from ..testset import QATestset
from .base import Metric

CORRECTNESS_EVALUATION_PROMPT = """Your role is to test AI assistants. Your task consists in assessing whether a assistant output correctly answers a question. 
You are provided with the ground truth answer to the question. Your task is then to evaluate if the assistant answer is close to the ground thruth answer. 

You are auditing the following assistant:
{assistant_description}

Here is the question that was asked to the assistant, its output, and the expected ground truth answer delimited with XML tags:
<question>
{question}
</question>

<assistant_answer>
{assistant_answer}
</assistant_answer>

<ground_truth>
{ground_truth}
</ground_truth>

Think step by step and consider the assistant output in its entirety. Remember: you need to have a strong and sound reason to support your evaluation.
If the assistant answer is correct, return True. If the assistant answer is incorrect, return False along with the reason.
You must output a single JSON object with keys 'correctness' and 'correctness_reason'. Make sure you return a valid JSON object."""


class CorrectnessMetric(Metric):
    def __init__(self, name: str, assistant_description: Optional[str] = None):
        self.name = name
        self.assistant_description = (
            assistant_description or "This assistant is a chatbot that answers question from users."
        )

    def __call__(self, testset: QATestset, answers: Sequence[str], llm_client: LLMClient) -> dict:
        results = []
        for sample, answer in zip(testset.to_pandas().reset_index().itertuples(), answers):
            try:
                out = llm_client.complete(
                    messages=[
                        LLMMessage(
                            role="user",
                            content=CORRECTNESS_EVALUATION_PROMPT.format(
                                assistant_description=self.assistant_description,
                                question=sample.question,
                                assistant_answer=answer,
                                ground_truth=sample.reference_answer,
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
