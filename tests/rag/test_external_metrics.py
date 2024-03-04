from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
from datasets import Dataset

from giskard.llm.client import LLMMessage
from giskard.rag.ragas_metrics import RagasEmbeddingsWrapper, RagasLLMWrapper, compute_ragas_metrics
from giskard.rag.testset import QATestset
from tests.rag.test_qa_testset import make_testset_df


def test_ragas_wrappers():
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(role="assistant", content="LLM response 1"),
        LLMMessage(role="assistant", content="LLM response 2"),
    ]
    llm_client.embeddings = Mock()
    llm_client.embeddings.side_effect = [np.array([[1, 2, 3]]), np.array([[4, 5, 6]])]

    ragas_llm = RagasLLMWrapper(llm_client)
    ragas_embedddings = RagasEmbeddingsWrapper(llm_client)

    prompt = Mock()
    prompt.to_string = Mock()
    prompt.to_string.return_value = "prompt"
    assert ragas_llm.generate_text(prompt).generations[0][0].text == "LLM response 1"
    assert ragas_llm.generate_text(prompt).generations[0][0].text == "LLM response 2"

    assert np.allclose(ragas_embedddings.embed_query("text"), np.array([1, 2, 3]))
    assert np.allclose(ragas_embedddings.embed_documents(["text"]), np.array([[4, 5, 6]]))


def test_compute_ragas_metrics():
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(role="assistant", content="LLM response 1"),
        LLMMessage(role="assistant", content="LLM response 2"),
    ]
    llm_client.embeddings = Mock()
    llm_client.embeddings.side_effect = [np.array([[1, 2, 3]]), np.array([[4, 5, 6]])]

    testset = QATestset(make_testset_df())
    answers = ["Default answer"] * 6

    def mock_evaluate(dataset, metrics, llm, embeddings):
        results = Mock()
        results.scores = Dataset.from_dict(
            {
                "context_precision": [0.1] * 6,
                "faithfulness": [0.2] * 6,
                "answer_relevancy": [0.3] * 6,
                "context_recall": [0.4] * 6,
            }
        )
        results.dataset = dataset
        results.to_pandas = Mock(return_value=pd.concat([dataset.to_pandas(), results.scores.to_pandas()], axis=1))

        return results

    with patch("giskard.rag.ragas_metrics.evaluate", new=mock_evaluate):
        ragas_metrics = compute_ragas_metrics(testset, answers, llm_client)

    assert "context_precision" in ragas_metrics.columns
    assert "faithfulness" in ragas_metrics.columns
    assert "answer_relevancy" in ragas_metrics.columns
    assert "context_recall" in ragas_metrics.columns
    assert "question" in ragas_metrics.columns

    assert len(ragas_metrics) == 6
    assert np.allclose(ragas_metrics["context_precision"], 0.1)
    assert np.allclose(ragas_metrics["faithfulness"], 0.2)
    assert np.allclose(ragas_metrics["answer_relevancy"], 0.3)
    assert np.allclose(ragas_metrics["context_recall"], 0.4)
