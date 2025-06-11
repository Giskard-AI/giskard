import uuid
from unittest.mock import Mock, patch

import numpy as np
from bokeh.plotting import figure

from giskard.rag import QATestset, RAGReport
from giskard.rag.base import AgentAnswer
from giskard.rag.knowledge_base import KnowledgeBase
from tests.rag.test_qa_testset import make_testset_samples
from tests.utils import DummyEmbedding

TEST_UUIDS = ["{}".format(i) for i in range(6)]


def _create_test_data(with_documents=False):
    """Helper to create a default testset, answers and metrics_results used across tests."""
    testset = QATestset(make_testset_samples())
    answers = [
        AgentAnswer(
            message="Default answer",
            documents=["Doc 1: example", "Doc 2: example"] if with_documents else None,
        )
    ] * 6
    metrics_results = {
        "1": {
            "correctness": True,
            "context_precision": 0.1,
            "faithfulness": 0.2,
            "answer_relevancy": 0.3,
            "context_recall": 0.4,
        },
        "2": {
            "correctness": True,
            "context_precision": 0.1,
            "faithfulness": 0.2,
            "answer_relevancy": 0.3,
            "context_recall": 0.4,
        },
        "3": {
            "correctness": False,
            "context_precision": 0.1,
            "faithfulness": 0.2,
            "answer_relevancy": 0.3,
            "context_recall": 0.4,
        },
        "4": {
            "correctness": True,
            "context_precision": 0.1,
            "faithfulness": 0.2,
            "answer_relevancy": 0.3,
            "context_recall": 0.4,
        },
        "5": {
            "correctness": False,
            "context_precision": 0.1,
            "faithfulness": 0.2,
            "answer_relevancy": 0.3,
            "context_recall": 0.4,
        },
        "6": {
            "correctness": False,
            "context_precision": 0.1,
            "faithfulness": 0.2,
            "answer_relevancy": 0.3,
            "context_recall": 0.4,
        },
    }
    return testset, answers, metrics_results


def _create_knowledge_base(testset, llm_client=None, embeddings=None):
    """Helper to create a KnowledgeBase from a given testset."""
    return KnowledgeBase(testset.to_pandas(), llm_client=llm_client, embedding_model=embeddings)


def test_report_plots():
    testset, answers, metrics_results = _create_test_data()

    knowledge_base = Mock()

    report = RAGReport(testset, answers, metrics_results, knowledge_base)
    plot = report.plot_correctness_by_metadata(metadata_name="question_type")
    assert isinstance(plot, figure)

    plot = report.plot_metrics_hist("context_precision", filter_metadata={"question_type": ["simple"]})
    assert isinstance(plot, figure)

    histograms = report.get_metrics_histograms()
    assert "Overall" in histograms
    assert "Question" in histograms
    assert "Topics" in histograms

    assert len(histograms["Overall"]["Overall"]) == 4
    assert len(histograms["Question"]) == 4
    assert len(histograms["Topics"]) == 2
    assert len(histograms["Topics"]["Cheese_1"]) == 4
    assert len(histograms["Question"]["simple"]) == 4


def test_report_to_html_with_embed():
    """Test that to_html works correctly with embed=True parameter."""
    testset, answers, metrics_results = _create_test_data()
    knowledge_base = Mock()

    report = RAGReport(testset, answers, metrics_results, knowledge_base)

    # Test to_html with embed=False (default behavior)
    html_output = report.to_html(embed=False)
    assert html_output is not None
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")

    # Test to_html with embed=True
    embedded_output = report.to_html(embed=True)
    assert embedded_output is not None

    # When embed=True, it should return an IPython HTML display object
    from IPython.core.display import HTML

    assert isinstance(embedded_output, HTML)

    # The embedded output should contain an iframe with the escaped HTML content
    iframe_html = embedded_output.data
    assert "<iframe" in iframe_html
    assert "srcdoc=" in iframe_html
    assert "width=100%" in iframe_html
    assert "height=800px" in iframe_html


def test_report_save_load(tmp_path):
    testset, answers, metrics_results = _create_test_data(with_documents=True)
    llm_client = Mock()

    embeddings = Mock()
    embeddings.embed.return_value = np.random.randn(len(testset), 8)

    with patch.object(uuid, "uuid4", side_effect=TEST_UUIDS):
        knowledge_base = _create_knowledge_base(testset, llm_client, embeddings)
    knowledge_base._topics_inst = {0: "Cheese_1", 1: "Cheese_2"}

    for doc_idx, doc in enumerate(knowledge_base._documents):
        doc.topic_id = 0 if doc_idx < 3 else 1
        doc.reduced_embeddings = np.random.randn(8)

    report = RAGReport(testset, answers, metrics_results, knowledge_base)

    report.save(tmp_path)
    loaded_report = RAGReport.load(tmp_path, llm_client=llm_client, embedding_model=DummyEmbedding())

    assert all(
        [
            doc.content == loaded_doc.content
            for doc, loaded_doc in zip(report._knowledge_base._documents, loaded_report._knowledge_base._documents)
        ]
    )
    assert report._knowledge_base.topics == loaded_report._knowledge_base.topics

    assert len(report._testset._dataframe) == len(loaded_report._testset._dataframe)
    assert len(report._metrics_results) == len(loaded_report._metrics_results)
    assert report._metrics_results["1"]["context_precision"] == loaded_report._metrics_results["1"]["context_precision"]
    assert all(
        [
            report._metrics_results[idx]["correctness"] == loaded_report._metrics_results[idx]["correctness"]
            for idx in report._metrics_results
        ]
    )
    assert all(report._dataframe["agent_answer"] == loaded_report._dataframe["agent_answer"])
    assert report._model_outputs == loaded_report._model_outputs


def test_report_save_load_without_knowledge_base(tmp_path):
    testset, answers, metrics_results = _create_test_data(with_documents=True)
    llm_client = Mock()

    embeddings = Mock()
    embeddings.embed.return_value = np.random.randn(len(testset), 8)

    report = RAGReport(testset, answers, metrics_results)

    report.save(tmp_path)
    loaded_report = RAGReport.load(tmp_path, llm_client=llm_client, embedding_model=DummyEmbedding())

    assert report._knowledge_base is None
    assert len(report._testset._dataframe) == len(loaded_report._testset._dataframe)
    assert len(report._metrics_results) == len(loaded_report._metrics_results)
    assert report._metrics_results["1"]["context_precision"] == loaded_report._metrics_results["1"]["context_precision"]
    assert all(
        [
            report._metrics_results[idx]["correctness"] == loaded_report._metrics_results[idx]["correctness"]
            for idx in report._metrics_results
        ]
    )
    assert all(report._dataframe["agent_answer"] == loaded_report._dataframe["agent_answer"])
    assert report._model_outputs == loaded_report._model_outputs
