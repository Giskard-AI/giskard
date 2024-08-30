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


def test_report_plots():
    knowledge_base = Mock()

    testset = QATestset(make_testset_samples())

    answers = [AgentAnswer(message="Default answer")] * 6

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


def test_report_save_load(tmp_path):
    question_samples = make_testset_samples()
    testset = QATestset(question_samples)
    llm_client = Mock()

    embeddings = Mock()
    embeddings.embed.return_value = np.random.randn(len(testset), 8)

    with patch.object(uuid, "uuid4", side_effect=TEST_UUIDS):
        knowledge_base = KnowledgeBase(testset.to_pandas(), llm_client=llm_client, embedding_model=embeddings)
    knowledge_base._topics_inst = {0: "Cheese_1", 1: "Cheese_2"}
    for doc_idx, doc in enumerate(knowledge_base._documents):
        if doc_idx < 3:
            doc.topic_id = 0
        else:
            doc.topic_id = 1
        doc.reduced_embeddings = np.random.randn(8)

    knowledge_base._documents

    answers = [AgentAnswer(message="Default answer", documents=["Doc 1: example", "Doc 2: example"])] * 6

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
