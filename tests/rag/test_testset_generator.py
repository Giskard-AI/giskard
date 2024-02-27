from unittest.mock import Mock

import numpy as np
import pandas as pd

from giskard.llm.client import LLMMessage
from giskard.rag import TestsetGenerator
from giskard.rag.knowledge_base import Document, KnowledgeBase


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

    return KnowledgeBase(knowledge_base_df, **kwargs)


def make_testset_generator():
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
            content="""{"question": "Where is Camembert from?",
                                                    "answer": "Camembert was created in Normandy, in the northwest of France."}""",
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
    kb_embeddings = np.ones((4, embedding_dimension)) * np.arange(4)[:, None] / 100
    query_embeddings = np.ones((3, embedding_dimension)) * np.array([0.02, 10, 15])[:, None]

    llm_client.embeddings.side_effect = [kb_embeddings]

    knowledge_base_df = make_knowledge_base(llm_client=llm_client, context_neighbors=3)

    testset_generator = TestsetGenerator(
        knowledge_base_df,
        assistant_description="This is a model for testing purpose.",
        llm_client=llm_client,
    )
    testset_generator.knowledge_base._rng = Mock()
    testset_generator.knowledge_base._rng.choice = Mock()
    testset_generator.knowledge_base._rng.choice.side_effect = (
        list(query_embeddings) + [Document({"content": "Distracting content"})] + list(query_embeddings)
    )

    return testset_generator


CONTEXT_STRING = """
------
Scamorza is a Southern Italian cow's milk cheese.
------
Bleu d'Auvergne is a French blue cheese, named for its place of origin in the Auvergne region.
------
Freeriding is a style of snowboarding or skiing performed on natural, un-groomed terrain, without a set course, goals or rules.
------
"""


def test_testset_generation():
    testset_generator = make_testset_generator()

    assert testset_generator.base_generator._knowledge_base._index.d == 8
    assert testset_generator.base_generator._knowledge_base._embeddings.shape == (4, 8)
    assert len(testset_generator.base_generator._knowledge_base._documents) == 4
    assert testset_generator.base_generator._knowledge_base._documents[2].content.startswith(
        "Scamorza is a Southern Italian cow's milk cheese."
    )

    test_set = testset_generator.generate_testset(num_questions=2)

    assert len(test_set) == 2

    df = test_set.to_pandas()

    assert df.iloc[0]["question"] == "Where is Camembert from?"
    assert df.iloc[0]["reference_answer"] == "Camembert was created in Normandy, in the northwest of France."
    assert df.iloc[0]["reference_context"] == CONTEXT_STRING

    assert df.iloc[1]["question"] == "Where is Camembert from?"
    assert df.iloc[1]["reference_context"] == "\n------\n"


def test_testset_question_types():
    testset_generator = make_testset_generator()
    testset = testset_generator.generate_testset(num_questions=1, question_types=[1, 2, 3, 4, 5, 6])
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
