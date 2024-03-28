from unittest.mock import MagicMock, Mock

import numpy as np
import pandas as pd
import pytest

from giskard.llm.client.base import ChatMessage
from giskard.rag import KnowledgeBase, QATestset, evaluate
from tests.rag.test_qa_testset import make_testset_df


def test_evaluate_from_answers():
    knowledge_base = MagicMock(KnowledgeBase)
    knowledge_base._documents = []
    answers = ["Default answer"] * 6

    with pytest.raises(ValueError, match="At least one of testset or knowledge base must be provided."):
        report = evaluate(answers)

    testset = QATestset(make_testset_df())
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""This is a recommendation test.""",
        ),
    ]

    report = evaluate(answers, testset, knowledge_base, llm_client=llm_client)
    assert len(report.failures) == 3
    assert len(report.get_failures(topic="Cheese_1")) == 1
    assert len(report.get_failures(topic="Cheese_2")) == 2

    assert len(report.get_failures(question_type="simple")) == 1
    assert len(report.get_failures(question_type="complex")) == 0
    assert len(report.get_failures(question_type="cheese")) == 0

    assert len(report.correctness_by_topic()) == 2
    assert np.isclose(report.correctness_by_topic().loc["Cheese_1"], 0.75)
    assert np.isclose(report.correctness_by_topic().loc["Cheese_2"], 0)

    assert len(report.correctness_by_question_type()) == 4
    assert np.isclose(report.correctness_by_question_type().loc["simple"], 2 / 3)
    assert np.isclose(report.correctness_by_question_type().loc["complex"], 1)

    assert len(report.component_scores()) == 5
    assert np.isclose(report.component_scores().loc["GENERATOR"], 1 / 3 + 2 / 9)
    assert np.isclose(report.component_scores().loc["RETRIEVER"], 1 / 3)

    assert report._recommendation == "This is a recommendation test."


def test_evaluate_from_answer_fn():
    knowledge_base = MagicMock(KnowledgeBase)
    knowledge_base._documents = []

    def answer_fn(message, history=None):
        if history:
            return "Conversation answer"
        return "Cheesy answer"

    testset = QATestset(make_testset_df())
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""This is a recommendation test.""",
        ),
    ]

    report = evaluate(answer_fn, testset, knowledge_base, llm_client=llm_client)
    assert len(report.failures) == 3
    assert len(report.get_failures(topic="Cheese_1")) == 1
    assert len(report.get_failures(topic="Cheese_2")) == 2
    assert report._answers == ["Cheesy answer"] * 5 + ["Conversation answer"]

    assert len(report.get_failures(question_type="simple")) == 1
    assert len(report.get_failures(question_type="complex")) == 0
    assert len(report.get_failures(question_type="cheese")) == 0

    assert len(report.correctness_by_topic()) == 2
    assert np.isclose(report.correctness_by_topic().loc["Cheese_1"], 0.75)
    assert np.isclose(report.correctness_by_topic().loc["Cheese_2"], 0)

    assert len(report.correctness_by_question_type()) == 4
    assert np.isclose(report.correctness_by_question_type().loc["simple"], 2 / 3)
    assert np.isclose(report.correctness_by_question_type().loc["complex"], 1)

    assert len(report.component_scores()) == 5
    assert np.isclose(report.component_scores().loc["GENERATOR"], 1 / 3 + 2 / 9)
    assert np.isclose(report.component_scores().loc["RETRIEVER"], 1 / 3)

    # Without conversation support
    def answer_fn_no_conv(message):
        return "ANSWER"

    testset = QATestset(make_testset_df())
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The agent answer is correct."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The agent answer is incorrect."}""",
        ),
        ChatMessage(
            role="assistant",
            content="""This is a recommendation test.""",
        ),
    ]

    report = evaluate(answer_fn, testset, knowledge_base, llm_client=llm_client)
    assert len(report.failures) == 3


def make_conversation_testset_df():
    return pd.DataFrame(
        [
            {
                "id": "1",
                "question": "Which milk is used to make Camembert?",
                "reference_answer": "Cow's milk is used to make Camembert.",
                "reference_context": "Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.",
                "conversation_history": [
                    dict(role="user", content="Hello, this is the conversation history."),
                    dict(role="assistant", content="How can I help you with that?"),
                ],
                "metadata": {"question_type": 5, "topic": "Cheese_1"},
            },
            {
                "id": "2",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [
                    dict(role="user", content="Hello, this is the conversation history."),
                    dict(role="assistant", content="How can I help you with that?"),
                ],
                "metadata": {"question_type": 5, "topic": "Cheese_2"},
            },
            {
                "id": "3",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [
                    dict(role="user", content="Hello, this is the conversation history."),
                    dict(role="assistant", content="How can I help you with that?"),
                ],
                "metadata": {"question_type": 5, "topic": "Cheese_1"},
            },
        ]
    )


def test_user_friendly_error_if_parameters_are_swapped():
    llm_client = MagicMock()
    llm_client.embeddings.side_effect = [np.random.rand(6, 10)]
    knowledge_base = KnowledgeBase.from_pandas(df=pd.DataFrame({"text": ["test"] * 6}), llm_client=llm_client)
    testset = QATestset(make_testset_df())

    with pytest.raises(ValueError, match="must be a KnowledgeBase object"):
        evaluate([], knowledge_base, testset, llm_client=llm_client)
