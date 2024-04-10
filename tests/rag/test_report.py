from unittest.mock import Mock

import numpy as np
import pandas as pd
from bokeh.plotting import figure

from giskard.rag import QATestset, RAGReport
from giskard.rag.knowledge_base import KnowledgeBase
from tests.rag.test_qa_testset import make_testset_df
from tests.utils import DummyEmbedding


def test_report_plots():
    knowledge_base = Mock()

    testset = QATestset(make_testset_df())

    answers = ["Default answer"] * 6

    eval_results = [
        {"id": "1", "correctness": True, "reason": "The agent answer is correct."},
        {"id": "2", "correctness": True, "reason": "The agent answer is correct."},
        {"id": "3", "correctness": False, "reason": "The agent answer is incorrect."},
        {"id": "4", "correctness": True, "reason": "The agent answer is correct."},
        {"id": "5", "correctness": False, "reason": "The agent answer is incorrect."},
        {"id": "6", "correctness": False, "reason": "The agent answer is incorrect."},
    ]

    metrics_results = {
        "correctness": pd.DataFrame(eval_results).set_index("id"),
        "context_precision": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "context_precision": [0.1] * 6}
        ).set_index("id"),
        "faithfulness": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "faithfulness": [0.2] * 6}
        ).set_index("id"),
        "answer_relevancy": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "answer_relevancy": [0.3] * 6}
        ).set_index("id"),
        "context_recall": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "context_recall": [0.4] * 6}
        ).set_index("id"),
    }

    report = RAGReport(testset, answers, metrics_results, knowledge_base)
    plot = report.plot_correctness_by_metadata(metadata_name="question_type")
    assert isinstance(plot, figure)

    plot = report.plot_metrics_hist("context_precision", filter_metadata={"question_type": ["simple"]})
    assert isinstance(plot, figure)

    additional_metrics, histograms = report.get_metrics_histograms()
    assert additional_metrics
    assert "Overall" in histograms
    assert "Question" in histograms
    assert "Topics" in histograms

    assert len(histograms["Overall"]["Overall"]) == 4
    assert len(histograms["Question"]) == 4
    assert len(histograms["Topics"]) == 2
    assert len(histograms["Topics"]["Cheese_1"]) == 4
    assert len(histograms["Question"]["simple"]) == 4


def test_report_save_load(tmp_path):
    df = make_testset_df()
    llm_client = Mock()

    embeddings = Mock()
    embeddings.embed.return_value = np.random.randn(len(df), 8)

    knowledge_base = KnowledgeBase(df, llm_client=llm_client, embedding_model=embeddings)
    knowledge_base._topics_inst = {0: "Cheese_1", 1: "Cheese_2"}
    for doc_idx, doc in enumerate(knowledge_base._documents):
        if doc_idx < 3:
            doc.topic_id = 0
        else:
            doc.topic_id = 1

    knowledge_base._documents

    testset = QATestset(make_testset_df())

    answers = ["Default answer"] * 6

    answers = ["Default answer"] * 6

    eval_results = [
        {"id": "1", "correctness": True, "reason": "The agent answer is correct."},
        {"id": "2", "correctness": True, "reason": "The agent answer is correct."},
        {"id": "3", "correctness": False, "reason": "The agent answer is incorrect."},
        {"id": "4", "correctness": True, "reason": "The agent answer is correct."},
        {"id": "5", "correctness": False, "reason": "The agent answer is incorrect."},
        {"id": "6", "correctness": False, "reason": "The agent answer is incorrect."},
    ]

    metrics_results = {
        "correctness": pd.DataFrame(eval_results).set_index("id"),
        "context_precision": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "context_precision": [0.1] * 6}
        ).set_index("id"),
        "faithfulness": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "faithfulness": [0.2] * 6}
        ).set_index("id"),
        "answer_relevancy": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "answer_relevancy": [0.3] * 6}
        ).set_index("id"),
        "context_recall": pd.DataFrame.from_dict(
            {"id": ["1", "2", "3", "4", "5", "6"], "context_recall": [0.4] * 6}
        ).set_index("id"),
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
    assert (
        report._metrics_results["context_precision"].loc["1", "context_precision"]
        == loaded_report._metrics_results["context_precision"].loc["1", "context_precision"]
    )
    assert all(report._metrics_results["correctness"] == loaded_report._metrics_results["correctness"])
    assert all(report._dataframe["agent_answer"] == loaded_report._dataframe["agent_answer"])
