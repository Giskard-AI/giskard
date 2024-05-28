import logging
from unittest.mock import MagicMock, Mock, patch

from giskard.rag.base import AgentAnswer

logger = logging.getLogger(__name__)


@patch("giskard.rag.metrics.ragas_metrics.RagasLLMWrapper")
@patch("giskard.rag.metrics.ragas_metrics.RagasEmbeddingsWrapper")
def test_ragas_metric_computation(ragas_llm_wrapper, ragas_embeddings_wrapper):
    from giskard.rag.metrics.ragas_metrics import RagasMetric

    ragas_metric = MagicMock()
    ragas_metric.score.return_value = 0.5
    metric = RagasMetric("test", ragas_metric, llm_client=Mock(), embedding_model=Mock())

    question_sample = {"question": "What is the capital of France?", "reference_answer": "Paris"}
    answer = AgentAnswer("The capital of France is Paris.")
    result = metric(question_sample, answer)

    assert result == {"test": 0.5}


@patch("giskard.rag.metrics.ragas_metrics.RagasLLMWrapper")
@patch("giskard.rag.metrics.ragas_metrics.RagasEmbeddingsWrapper")
def test_ragas_metric_computation_with_context(ragas_llm_wrapper, ragas_embeddings_wrapper):
    from giskard.rag.metrics.ragas_metrics import RagasMetric

    ragas_metric = MagicMock()
    ragas_metric.score.return_value = 0.5
    metric = RagasMetric("test", ragas_metric, requires_context=True, llm_client=Mock(), embedding_model=Mock())

    question_sample = {"question": "What is the capital of France?", "reference_answer": "Paris"}
    answer = AgentAnswer("The capital of France is Paris.", documents=["Paris"])
    result = metric(question_sample, answer)

    assert result == {"test": 0.5}


@patch("giskard.rag.metrics.ragas_metrics.RagasLLMWrapper")
@patch("giskard.rag.metrics.ragas_metrics.RagasEmbeddingsWrapper")
def test_ragas_metric_computation_with_missing_context(ragas_llm_wrapper, ragas_embeddings_wrapper, caplog):
    from giskard.rag.metrics.ragas_metrics import RagasMetric

    ragas_metric = MagicMock()
    ragas_metric.score.return_value = 0.5
    metric = RagasMetric("test", ragas_metric, requires_context=True, llm_client=Mock(), embedding_model=Mock())

    question_sample = {"question": "What is the capital of France?", "reference_answer": "Paris"}
    answer = AgentAnswer("The capital of France is Paris.")

    with caplog.at_level(logging.WARNING):
        result = metric(question_sample, answer)
        assert result == {"test": 0.0}
        assert "No retrieved documents are passed to the evaluation function" in caplog.text
