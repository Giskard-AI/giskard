from typing import Callable, Optional, Sequence, Union

import logging

from ..llm.client import LLMClient, get_default_client
from .knowledge_base import KnowledgeBase
from .metrics import CorrectnessMetric, Metric
from .question_generators.utils import maybe_tqdm
from .recommendation import get_rag_recommendation
from .report import RAGReport
from .testset import QATestset
from .testset_generation import generate_testset

logger = logging.getLogger(__name__)


def evaluate(
    answers_fn: Union[Callable, Sequence[str]],
    knowledge_base: Optional[KnowledgeBase] = None,
    testset: Optional[QATestset] = None,
    llm_client: Optional[LLMClient] = None,
    assistant_description: str = "This assistant is a chatbot that answers question from users.",
    additional_metrics: Optional[Sequence[Metric]] = None,
    conversation_support: bool = False,
) -> RAGReport:
    """
    Evaluate an assistant by comparing its answers on a QATestset

    Parameters
    ----------
    answers_fn : Union[Callable, Sequence[str]]
        The prediction function of the assistant to evaluate or the list its answers on the testset.
    knowledge_base : KnowledgeBase, optional
        The knowledge base of the assistant to evaluate. If not provided, a testset must be provided.
    testset : QATestset, optional
        The test set to evaluate the assistant on. If not provided, a knowledge base must be provided and a default testset will be created from the knowledge base.
        Note that if the answers_fn is a list of answers, the testset is required.
    llm_client : LLMClient, optional
        The LLM client to use for the evaluation. If not provided, a default openai client will be used.
    assistant_description : str, optional
        Description of the assistant to be tested.
    additional_metrics : Optional[Sequence[Metric]], optional
        The metrics to compute on the test set. If not provided, only the correctness of the answers will be computed.
    conversation_support : bool, optional
        Whether the assistant supports conversational questions or not. By default False.


    Returns
    -------
    RAGReport
        The report of the evaluation.
    """

    if testset is None and knowledge_base is None:
        raise ValueError("At least one of testset or knowledge base must be provided to the evaluate function.")

    if testset is None and not isinstance(answers_fn, Sequence):
        raise ValueError(
            "If the testset is not provided, the answers_fn must be a list of answers to ensure the matching between questions and answers."
        )

    if testset is None:
        testset = generate_testset(knowledge_base)

    answers = (
        answers_fn
        if isinstance(answers_fn, Sequence)
        else make_predictions(answers_fn, testset, conversation_support=conversation_support)
    )

    llm_client = llm_client or get_default_client()

    metrics = [CorrectnessMetric(name="Correctness", assistant_description=assistant_description)]
    if additional_metrics:
        metrics.extend(additional_metrics)

    metrics_results = {}
    for metric in metrics:
        metrics_results.update(metric(testset, answers, llm_client))

    report = RAGReport(testset, answers, metrics_results, knowledge_base)
    recommendation = get_rag_recommendation(
        report.topics,
        report.correctness_by_question_type().to_dict()["correctness"],
        report.correctness_by_topic().to_dict()["correctness"],
        llm_client,
    )
    report._recommendation = recommendation
    return report


def make_predictions(answers_fn, testset, conversation_support=False):
    answers = []
    logger.info("Starting to make predictions on the test set.")
    for sample in maybe_tqdm(
        testset.to_pandas().itertuples(), desc="Asking questions to the assistant", total=len(testset)
    ):
        if conversation_support and len(sample.conversation_history) > 0:
            answers.append(answers_fn(sample.question, sample.conversation_history))
        else:
            answers.append(answers_fn(sample.question))
    logger.info("Predictions finished. Starting evaluation.")
    return answers
