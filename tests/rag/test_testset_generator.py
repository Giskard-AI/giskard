from unittest.mock import Mock

import numpy as np
import pandas as pd

from giskard.llm.client import LLMMessage
from giskard.rag.knowledge_base import Document, KnowledgeBase
from giskard.rag.question_generators import (
    complex_questions_modifier,
    conversational_questions_modifier,
    distracting_questions_modifier,
    double_questions_modifier,
    situational_questions_modifier,
)
from giskard.rag.testset_generation import generate_testset


def make_knowledge_base(**kwargs):
    knowledge_base_df = pd.DataFrame(
        [
            {"context": "Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese."},
            {
                "context": "Bleu d'Auvergne is a French blue cheese, named for its place of origin in the Auvergne region."
            },
            {"context": "Scamorza is a Southern Italian cow's milk cheese."},
            {
                "context": "Freeriding is a style of snowboarding or skiing performed on natural, un-groomed terrain, without a set course, goals or rules."
            },
        ]
    )
    knowledge = KnowledgeBase(knowledge_base_df, **kwargs)
    knowledge._topics_inst = ["cheese", "ski"]
    return knowledge


def make_testset_generation_inputs():
    llm_client = Mock()

    mock_llm_complete_simple = [
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is Camembert from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France."}""",
        )
    ]

    mock_llm_complete_complex = [
        LLMMessage(
            role="assistant",
            content="""{"question": "What is freeriding ski?",
                                                    "answer": "Freeriding is a style of snowboarding or skiing."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is Camembert from?"}""",
        ),
    ]

    mock_llm_complete_distracting = [
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is Camembert from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is Camembert from?"}""",
        ),
    ]

    mock_llm_complete_situation = [
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is Camembert from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""I am a cheese enthusiast and I want to know more about Camembert.""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"question": "I am a cheese enthusiast, where is Camembert from?"}""",
        ),
    ]

    mock_llm_complete_double = [
        LLMMessage(
            role="assistant",
            content="""[{"question": "1 Where is Camembert from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France."},
                                                    {"question": "Where is Scamorza from?",
                                                    "answer": "Scamorza is a cheese from southern Italy."}]""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"question": "2 Where are Camembert and Scamorza from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France, Scamorza is a cheese from southern Italy."}""",
        ),
    ]

    mock_llm_complete_conversation = [
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is Camembert from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France."}""",
        ),
        LLMMessage(
            role="assistant",
            content="""{"question": "Where is it from?",
                                                    "introduction": "Camembert is a cheese."}""",
        ),
    ]

    llm_client.complete.side_effect = [
        *mock_llm_complete_simple,
        *mock_llm_complete_complex,
        *mock_llm_complete_distracting,
        *mock_llm_complete_situation,
        *mock_llm_complete_double,
        *mock_llm_complete_conversation,
    ]

    embedding_dimension = 8

    llm_client.embeddings = Mock()
    # evenly spaced embeddings for the knowledge base elements and specifically chosen embeddings for
    # each mock embedding calls.
    kb_embeddings = np.ones((4, embedding_dimension)) * np.array([0, 1, 2, 20])[:, None] / 100

    llm_client.embeddings.side_effect = [kb_embeddings]

    knowledge_base = make_knowledge_base(llm_client=llm_client, context_neighbors=3)
    for doc, topic_id in zip(knowledge_base._documents, [0, 0, 0, 1]):
        doc.topic_id = topic_id

    knowledge_base._rng = Mock()
    knowledge_base._rng.choice = Mock()
    knowledge_base._rng.choice.side_effect = [
        2,
        3,
        3,
        Document({"content": "Distracting content"}),
        2,
        3,
        3,
    ]

    return llm_client, knowledge_base


CONTEXT_STRING = """
------
Scamorza is a Southern Italian cow's milk cheese.
------
Bleu d'Auvergne is a French blue cheese, named for its place of origin in the Auvergne region.
------
Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.
------
"""


def test_testset_generation():
    llm_client, knowledge_base = make_testset_generation_inputs()

    test_set = generate_testset(knowledge_base=knowledge_base, num_questions=2, llm_client=llm_client)

    assert len(test_set) == 2

    df = test_set.to_pandas()
    assert df.iloc[0]["question"] == "Where is Camembert from?"
    assert df.iloc[0]["reference_answer"] == "Camembert was created in Normandy, in the northwest of France."
    assert df.iloc[0]["reference_context"] == CONTEXT_STRING
    assert df.iloc[0]["metadata"]["question_type"] == 1
    assert df.iloc[0]["conversation_history"] == []
    assert df.iloc[0]["metadata"]["topic"] == "cheese"

    assert df.iloc[1]["question"] == "What is freeriding ski?"
    assert (
        df.iloc[1]["reference_context"]
        == "\n------\nFreeriding is a style of snowboarding or skiing performed on natural, un-groomed terrain, without a set course, goals or rules.\n------\n"
    )
    assert df.iloc[1]["metadata"]["topic"] == "ski"


def test_testset_question_types():
    llm_client, knowledge_base = make_testset_generation_inputs()
    testset = generate_testset(
        knowledge_base=knowledge_base,
        llm_client=llm_client,
        num_questions=1,
        question_generators=[
            complex_questions_modifier,
            distracting_questions_modifier,
            situational_questions_modifier,
            double_questions_modifier,
            conversational_questions_modifier,
        ],
    )
    assert len(testset._dataframe["metadata"]) == 6
    for idx, row_id in enumerate(testset.to_pandas().index):
        assert testset._dataframe["metadata"][row_id]["question_type"] == idx + 1
        if testset._dataframe["metadata"][row_id]["question_type"] != 6:
            assert testset._dataframe["conversation_history"][row_id] == []
        else:
            assert testset._dataframe["conversation_history"][row_id] == [
                {"role": "user", "content": "Camembert is a cheese."}
            ]

    assert "distracting_context" in testset._dataframe["metadata"][2]
    assert testset._dataframe["metadata"][2]["distracting_context"] == "Distracting content"

    assert "situational_context" in testset._dataframe["metadata"][3]
    assert (
        testset._dataframe["metadata"][3]["situational_context"]
        == "I am a cheese enthusiast and I want to know more about Camembert."
    )

    assert "original_questions" in testset._dataframe["metadata"][4]
    assert testset._dataframe["metadata"][4]["original_questions"] == [
        {
            "question": "1 Where is Camembert from?",
            "answer": "Camembert was created in Normandy, in the northwest of France.",
        },
        {"question": "Where is Scamorza from?", "answer": "Scamorza is a cheese from southern Italy."},
    ]


def test_question_generation_fail(caplog):
    llm_client, knowledge_base = make_testset_generation_inputs()
    testset = generate_testset(
        knowledge_base=knowledge_base,
        llm_client=llm_client,
        num_questions=1,
        question_generators=[complex_questions_modifier, distracting_questions_modifier, Mock()],
    )

    assert "Encountered error in question generation" in caplog.text
    assert len(testset.to_pandas()) == 3
