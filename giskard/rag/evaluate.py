from typing import Callable, Optional, Sequence, Union

import logging
from inspect import signature

from ..llm.client import LLMClient, get_default_client
from ..utils.analytics_collector import analytics
from .knowledge_base import KnowledgeBase
from .metrics import CorrectnessMetric
from .question_generators.utils import maybe_tqdm
from .recommendation import get_rag_recommendation
from .report import RAGReport
from .testset import QATestset
from .testset_generation import generate_testset

logger = logging.getLogger(__name__)


def evaluate(
    answer_fn: Union[Callable, Sequence[str]],
    testset: Optional[QATestset] = None,
    knowledge_base: Optional[KnowledgeBase] = None,
    llm_client: Optional[LLMClient] = None,
    agent_description: str = "This agent is a chatbot that answers question from users.",
    metrics: Optional[Sequence[Callable]] = None,
) -> RAGReport:
    """Evaluate an agent by comparing its answers on a QATestset.

    Parameters
    ----------
    answers_fn : Union[Callable, Sequence[str]]
        The prediction function of the agent to evaluate or a list of precalculated answers on the testset.
    testset : QATestset, optional
        The test set to evaluate the agent on. If not provided, a knowledge base must be provided and a default testset will be created from the knowledge base.
        Note that if the answers_fn is a list of answers, the testset is required.
    knowledge_base : KnowledgeBase, optional
        The knowledge base of the agent to evaluate. If not provided, a testset must be provided.
    llm_client : LLMClient, optional
        The LLM client to use for the evaluation. If not provided, a default openai client will be used.
    agent_description : str, optional
        Description of the agent to be tested.
    metrics : Optional[Sequence[Callable]], optional
        Metrics to compute on the test set.

    Returns
    -------
    RAGReport
        The report of the evaluation.
    """
    if testset is None and knowledge_base is None:
        raise ValueError("At least one of testset or knowledge base must be provided to the evaluate function.")

    if testset is None and not isinstance(answer_fn, Sequence):
        raise ValueError(
            "If the testset is not provided, the answer_fn must be a list of answers to ensure the matching between questions and answers."
        )

    # Check basic types, in case the user passed the params in the wrong order
    if knowledge_base is not None and not isinstance(knowledge_base, KnowledgeBase):
        raise ValueError(
            f"knowledge_base must be a KnowledgeBase object (got {type(knowledge_base)} instead). Are you sure you passed the parameters in the right order?"
        )

    if testset is not None and not isinstance(testset, QATestset):
        raise ValueError(
            f"testset must be a QATestset object (got {type(testset)} instead). Are you sure you passed the parameters in the right order?"
        )

    if testset is None:
        testset = generate_testset(knowledge_base)

    answers = answer_fn if isinstance(answer_fn, Sequence) else _compute_answers(answer_fn, testset)

    llm_client = llm_client or get_default_client()

    # @TODO: improve this
    metrics = metrics or []
    if not any(isinstance(metric, CorrectnessMetric) for metric in metrics):
        metrics.append(CorrectnessMetric(name="Correctness", agent_description=agent_description))

    metrics_results = {}
    for metric in metrics:
        metrics_results.update(metric(testset, answers, llm_client=llm_client))

    report = RAGReport(testset, answers, metrics_results, knowledge_base)
    recommendation = get_rag_recommendation(
        report.topics,
        report.correctness_by_question_type().to_dict()["correctness"],
        report.correctness_by_topic().to_dict()["correctness"],
        llm_client,
    )
    report._recommendation = recommendation

    analytics.track(
        "raget:evaluation",
        {
            "testset_size": len(testset),
            "knowledge_base_size": len(knowledge_base) if knowledge_base else -1,
            "agent_description": agent_description,
            "num_metrics": len(metrics),
            "correctness": report.correctness,
        },
    )
    return report


def _compute_answers(answer_fn, testset):
    answers = []
    needs_history = len(signature(answer_fn).parameters) > 1
    for sample in maybe_tqdm(testset.samples, desc="Asking questions to the agent", total=len(testset)):
        kwargs = {}

        if needs_history:
            kwargs["history"] = sample["conversation_history"]

        answers.append(answer_fn(sample["question"], **kwargs))
    return answers
