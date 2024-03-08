from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from giskard.llm.client.base import LLMMessage
from giskard.rag import QATestset, evaluate
from tests.rag.test_qa_testset import make_testset_df


def test_evaluate_from_answers():
    knowledge_base = Mock()
    answers = ["Default answer"] * 6

    with pytest.raises(ValueError, match="At least one of testset or knowledge base must be provided."):
        report = evaluate(answers)

    testset = QATestset(make_testset_df())
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""This is a recommendation test.""",
        ),
    ]

    report = evaluate(answers, knowledge_base, testset, llm_client=llm_client)
    assert len(report.failures) == 3
    assert len(report.get_failures(topic="Cheese_1")) == 1
    assert len(report.get_failures(topic="Cheese_2")) == 2

    assert len(report.get_failures(question_type=1)) == 1
    assert len(report.get_failures(question_type=2)) == 0
    assert len(report.get_failures(question_type=100)) == 0

    assert len(report.correctness_by_topic()) == 2
    assert np.isclose(report.correctness_by_topic().loc["Cheese_1"], 0.75)
    assert np.isclose(report.correctness_by_topic().loc["Cheese_2"], 0)

    assert len(report.correctness_by_question_type()) == 4
    assert np.isclose(report.correctness_by_question_type().loc["EASY"], 2 / 3)
    assert np.isclose(report.correctness_by_question_type().loc["COMPLEX"], 1)

    assert len(report.component_scores()) == 5
    assert np.isclose(report.component_scores().loc["GENERATOR"], 1 / 3 + 2 / 9)
    assert np.isclose(report.component_scores().loc["RETRIEVER"], 1 / 3)

    assert report._recommendation == "This is a recommendation test."


def test_evaluate_from_answer_fn():
    knowledge_base = Mock()

    def answer_fn(message):
        return "Cheesy answer"

    testset = QATestset(make_testset_df())
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""This is a recommendation test.""",
        ),
    ]

    report = evaluate(answer_fn, knowledge_base, testset, llm_client=llm_client)
    assert len(report.failures) == 3
    assert len(report.get_failures(topic="Cheese_1")) == 1
    assert len(report.get_failures(topic="Cheese_2")) == 2

    assert len(report.get_failures(question_type=1)) == 1
    assert len(report.get_failures(question_type=2)) == 0
    assert len(report.get_failures(question_type=100)) == 0

    assert len(report.correctness_by_topic()) == 2
    assert np.isclose(report.correctness_by_topic().loc["Cheese_1"], 0.75)
    assert np.isclose(report.correctness_by_topic().loc["Cheese_2"], 0)

    assert len(report.correctness_by_question_type()) == 4
    assert np.isclose(report.correctness_by_question_type().loc["EASY"], 2 / 3)
    assert np.isclose(report.correctness_by_question_type().loc["COMPLEX"], 1)

    assert len(report.component_scores()) == 5
    assert np.isclose(report.component_scores().loc["GENERATOR"], 1 / 3 + 2 / 9)
    assert np.isclose(report.component_scores().loc["RETRIEVER"], 1 / 3)


def make_conversation_testset_df():
    return pd.DataFrame(
        [
            {
                "id": "1",
                "question": "Which milk is used to make Camembert?",
                "reference_answer": "Cow's milk is used to make Camembert.",
                "reference_context": "Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.",
                "conversation_history": [dict(role="user", content="Hello, this is the conversation history.")],
                "metadata": {"question_type": 5, "topic": "Cheese_1"},
            },
            {
                "id": "2",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [
                    dict(role="user", content="Hello, this is the conversation history."),
                    dict(role="user", content="Hello, this is the conversation history."),
                ],
                "metadata": {"question_type": 5, "topic": "Cheese_2"},
            },
            {
                "id": "3",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [dict(role="user", content="Hello, this is the conversation history.")],
                "metadata": {"question_type": 5, "topic": "Cheese_1"},
            },
        ]
    )


def test_evaluate_conversational_question():
    knowledge_base = Mock()

    testset = QATestset(make_conversation_testset_df())
    llm_client = Mock()
    llm_client.complete = Mock()
    llm_client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": true, "correctness_reason": "The assistant answer is correct."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"correctness": false, "correctness_reason": "The assistant answer is incorrect."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""This is a recommendation test.""",
        ),
    ]

    def answer_fn(messages):
        if messages[-1]["content"].startswith("Hello"):
            return "Conversation message"
        return "Cheesy answer"

    answer_fn = Mock(side_effect=answer_fn)

    report = evaluate(answer_fn, knowledge_base, testset, llm_client=llm_client, conversation_support=True)

    assert answer_fn.call_count == 7

    assert len(report.failures) == 1
    assert len(report.get_failures(topic="Cheese_1")) == 1
    assert len(report.get_failures(topic="Cheese_2")) == 0

    assert len(report.get_failures(question_type=5)) == 1
    assert len(report.get_failures(question_type=2)) == 0
