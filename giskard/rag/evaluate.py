from typing import Callable, Optional, Sequence, Union

import json
import logging

from ..llm.client import LLMClient, LLMMessage, get_default_client
from ..llm.errors import LLMGenerationError
from .knowledge_base import KnowledgeBase
from .report import RAGReport
from .testset import QATestset
from .testset_generator import generate_testset

logger = logging.getLogger(__name__)

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
You must output a single JSON object with keys 'evaluation' and 'reason'. Make sure you return a valid JSON object."""


def evaluate(
    answers_fn: Union[Callable, Sequence[str]],
    knowledge_base: KnowledgeBase = None,
    testset: Optional[QATestset] = None,
    llm_client: Optional[LLMClient] = None,
    assistant_description: str = "This assistant is a chatbot that answers question from users.",
    ragas_metrics: bool = False,
) -> RAGReport:
    if testset is None and knowledge_base is None:
        raise ValueError("At least one of testset or knowledge base must be provided.")

    if testset is None:
        testset = generate_testset(knowledge_base)

    def make_predictions(answers_fn, testset):
        return [answers_fn(question) for question in testset.to_pandas()["question"]]

    answers = answers_fn if isinstance(answers_fn, Sequence) else make_predictions(answers_fn, testset)

    llm_client = llm_client or get_default_client()

    results = []
    for testset_item, answer in zip(testset.to_pandas().itertuples(), answers):
        try:
            out = llm_client.complete(
                messages=[
                    LLMMessage(
                        role="user",
                        content=CORRECTNESS_EVALUATION_PROMPT.format(
                            assistant_description=assistant_description,
                            question=testset_item.question,
                            assistant_answer=answer,
                            ground_truth=testset_item.reference_answer,
                        ),
                    ),
                ],
                temperature=0,
            )
            evaluation = json.loads(out.content, strict=False)
            evaluation["assistant_answer"] = answer
            results.append(evaluation)
        except Exception as err:
            raise LLMGenerationError(f"Error while evaluating the assistant: {err}")

    if ragas_metrics:
        try:
            from .ragas_metrics import compute_ragas_metrics

            ragas_results = compute_ragas_metrics(testset, answers, llm_client)
        except ImportError as err:
            logger.error(
                f"Package {err.name} is missing, it is required for the computation of RAGAS metrics. You can install it with `pip install {err.name}`."
            )
            logger.error("Skipping RAGAS metrics computation.")
            ragas_results = None
        except Exception as err:
            logger.error(f"Encountered error during RAGAS metric computation: {err}. Skipping.")
            logger.exception(err)
            ragas_results = None
    # return RAGReport(results, testset, knowledge_base, ragas_metrics))
    return results, ragas_results
