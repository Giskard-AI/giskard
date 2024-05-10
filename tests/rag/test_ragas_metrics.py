import logging
import sys
from unittest.mock import MagicMock, patch

from giskard.rag.metrics.base import ModelOutput

sys.modules["ragas"] = MagicMock()
sys.modules["ragas.embeddings"] = MagicMock()
sys.modules["ragas.llms"] = MagicMock()
sys.modules["ragas.llms.prompt"] = MagicMock()
sys.modules["ragas.metrics"] = MagicMock()
sys.modules["ragas.metrics.base"] = MagicMock()
sys.modules["ragas.run_config"] = MagicMock()

logger = logging.getLogger(__name__)


@patch("giskard.rag.metrics.ragas_metrics.RagasLLMWrapper")
@patch("giskard.rag.metrics.ragas_metrics.RagasEmbeddingsWrapper")
def test_ragas_metric_computation(ragas_llm_wrapper, ragas_embeddings_wrapper):
    from giskard.rag.metrics.ragas_metrics import RagasMetric

    ragas_metric = MagicMock()
    ragas_metric.score.return_value = 0.5
    metric = RagasMetric("test", ragas_metric)

    question_sample = {"question": "What is the capital of France?", "reference_answer": "Paris"}
    answer = ModelOutput("The capital of France is Paris.")
    result = metric(question_sample, answer)

    assert result == {"test": 0.5}


@patch("giskard.rag.metrics.ragas_metrics.RagasLLMWrapper")
@patch("giskard.rag.metrics.ragas_metrics.RagasEmbeddingsWrapper")
def test_ragas_metric_computation_with_context(ragas_llm_wrapper, ragas_embeddings_wrapper):
    from giskard.rag.metrics.ragas_metrics import RagasMetric

    ragas_metric = MagicMock()
    ragas_metric.score.return_value = 0.5
    metric = RagasMetric("test", ragas_metric, requires_context=True)

    question_sample = {"question": "What is the capital of France?", "reference_answer": "Paris"}
    answer = ModelOutput("The capital of France is Paris.", documents=["Paris"])
    result = metric(question_sample, answer)

    assert result == {"test": 0.5}


@patch("giskard.rag.metrics.ragas_metrics.RagasLLMWrapper")
@patch("giskard.rag.metrics.ragas_metrics.RagasEmbeddingsWrapper")
def test_ragas_metric_computation_with_missing_context(ragas_llm_wrapper, ragas_embeddings_wrapper, caplog):
    from giskard.rag.metrics.ragas_metrics import RagasMetric

    ragas_metric = MagicMock()
    ragas_metric.score.return_value = 0.5
    metric = RagasMetric("test", ragas_metric, requires_context=True)

    question_sample = {"question": "What is the capital of France?", "reference_answer": "Paris"}
    answer = ModelOutput("The capital of France is Paris.")

    with caplog.at_level(logging.WARNING):
        result = metric(question_sample, answer)
        assert result == {"test": 0.0}
        assert "No retrieved documents are passed to the evaluation function" in caplog.text
