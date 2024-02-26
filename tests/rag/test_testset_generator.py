from unittest.mock import Mock

import numpy as np
import pandas as pd

from giskard.llm.client import LLMMessage
from giskard.rag import TestsetGenerator
from giskard.rag.vector_store import Document


def make_knowledge_base_df():
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
    return knowledge_base_df


def make_testset_generator():
    llm_client = Mock()
    llm_client.complete.side_effect = (
        [
            LLMMessage(
                role="assistant",
                content="""{"question": "Where is Camembert from?",
"answer": "Camembert was created in Normandy, in the northwest of France."}""",
            )
        ]
        * 5
    )

    embedding_dimension = 8

    llm_client.embeddings = Mock()
    # evenly spaced embeddings for the knowledge base elements and specifically chosen embeddings for
    # each mock embedding calls.
    kb_embeddings = np.ones((4, embedding_dimension)) * np.arange(4)[:, None] / 100
    query_embeddings = np.ones((3, embedding_dimension)) * np.array([0.02, 10, 15])[:, None]

    llm_client.embeddings.side_effect = [kb_embeddings]

    knowledge_base_df = make_knowledge_base_df()

    testset_generator = TestsetGenerator(
        knowledge_base_df,
        assistant_description="This is a model for testing purpose.",
        llm_client=llm_client,
        context_neighbors=3,
    )
    testset_generator.base_generator._rng = Mock()
    testset_generator.base_generator._rng.choice = Mock()
    testset_generator.base_generator._rng.choice.side_effect = list(query_embeddings) + [
        Document({"content": "Distracting content"})
    ]

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

    assert testset_generator.base_generator._vector_store.index.d == 8
    assert testset_generator.base_generator._vector_store.embeddings.shape == (4, 8)
    assert len(testset_generator.base_generator._vector_store.documents) == 4
    assert testset_generator.base_generator._vector_store.documents[2].content.startswith(
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


def test_testset_difficulty_levels():
    testset_generator = make_testset_generator()
    testset = testset_generator.generate_testset(num_questions=1, difficulty=[1, 2, 3])
    assert len(testset._dataframe["metadata"]) == 3
    for row_id in testset.to_pandas().index:
        assert testset._dataframe["metadata"][row_id]["difficulty"] in [1, 2, 3]
        if testset._dataframe["metadata"][row_id]["difficulty"] == 3:
            assert testset._dataframe["metadata"][row_id]["distracting_context"] == "Distracting content"
