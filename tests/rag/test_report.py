from unittest.mock import Mock

import pandas as pd
from bokeh.plotting import figure

from giskard.rag import QATestset, RAGReport
from giskard.rag.knowledge_base import KnowledgeBase
from tests.rag.test_qa_testset import make_testset_df


def test_report_plots():
    knowledge_base = Mock()

    testset = QATestset(make_testset_df())

    eval_results = [
        {"evaluation": True, "reason": "The assistant answer is correct.", "assistant_answer": "Default answer"},
        {"evaluation": True, "reason": "The assistant answer is correct.", "assistant_answer": "Default answer"},
        {"evaluation": False, "reason": "The assistant answer is incorrect.", "assistant_answer": "Default answer"},
        {"evaluation": True, "reason": "The assistant answer is correct.", "assistant_answer": "Default answer"},
        {"evaluation": False, "reason": "The assistant answer is incorrect.", "assistant_answer": "Default answer"},
        {"evaluation": False, "reason": "The assistant answer is incorrect.", "assistant_answer": "Default answer"},
    ]

    ragas_metrics = pd.DataFrame.from_dict(
        {
            "id": ["1", "2", "3", "4", "5", "6"],
            "context_precision": [0.1] * 6,
            "faithfulness": [0.2] * 6,
            "answer_relevancy": [0.3] * 6,
            "context_recall": [0.4] * 6,
        }
    )
    report = RAGReport(eval_results, testset, knowledge_base, ragas_metrics=ragas_metrics)

    plot = report.plot_correctness_by_metadata(metadata_name="question_type")
    assert isinstance(plot, figure)

    plot = report.plot_ragas_metrics_hist("context_precision", filter_metadata={"question_type": ["EASY"]})
    assert isinstance(plot, figure)

    histograms = report.get_ragas_histograms()
    assert "Overall" in histograms
    assert "Question" in histograms
    assert "Topics" in histograms

    assert len(histograms["Overall"]["Overall"]) == 4
    assert len(histograms["Question"]) == 4
    assert len(histograms["Topics"]) == 2
    assert len(histograms["Topics"]["Cheese_1"]) == 4
    assert len(histograms["Question"]["EASY"]) == 4


def test_report_save_load(tmp_path):
    knowledge_base = KnowledgeBase(make_testset_df())

    testset = QATestset(make_testset_df())

    eval_results = [
        {"evaluation": True, "reason": "The assistant answer is correct.", "assistant_answer": "Default answer"},
        {"evaluation": True, "reason": "The assistant answer is correct.", "assistant_answer": "Default answer"},
        {"evaluation": False, "reason": "The assistant answer is incorrect.", "assistant_answer": "Default answer"},
        {"evaluation": True, "reason": "The assistant answer is correct.", "assistant_answer": "Default answer"},
        {"evaluation": False, "reason": "The assistant answer is incorrect.", "assistant_answer": "Default answer"},
        {"evaluation": False, "reason": "The assistant answer is incorrect.", "assistant_answer": "Default answer"},
    ]

    ragas_metrics = pd.DataFrame.from_dict(
        {
            "id": ["1", "2", "3", "4", "5", "6"],
            "context_precision": [0.1] * 6,
            "faithfulness": [0.2] * 6,
            "answer_relevancy": [0.3] * 6,
            "context_recall": [0.4] * 6,
        }
    )

    report = RAGReport(eval_results, testset, knowledge_base, ragas_metrics=ragas_metrics)

    report.save(tmp_path)
    loaded_report = RAGReport.load(tmp_path)

    assert all(
        [
            doc.content == loaded_doc.content
            for doc, loaded_doc in zip(report._knowledge_base._documents, loaded_report._knowledge_base._documents)
        ]
    )
    assert report._knowledge_base.topics == loaded_report._knowledge_base.topics

    assert len(report._testset._dataframe) == len(loaded_report._testset._dataframe)
    assert len(report._ragas_metrics) == len(loaded_report._ragas_metrics)
    assert report._ragas_metrics.loc[1, "context_precision"] == loaded_report._ragas_metrics.loc[1, "context_precision"]
    assert report._results[0]["evaluation"] == loaded_report._results[0]["evaluation"]
    assert report._results[0]["reason"] == loaded_report._results[0]["reason"]
    assert report._results[0]["assistant_answer"] == loaded_report._results[0]["assistant_answer"]
