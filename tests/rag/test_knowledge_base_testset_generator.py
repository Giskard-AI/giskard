from unittest.mock import Mock

import numpy as np
import pandas as pd

from giskard.llm.client import LLMMessage
from giskard.rag import KnowledgeBaseTestsetGenerator


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
    llm_client = Mock()
    llm_client.complete.side_effect = (
        [
            LLMMessage(
                role="assistant",
                content="""{"question": "Where is Camembert from?",
"answer": "Camembert was created in Normandy, in the northwest of France."}""",
            )
        ]
        * 2
    )

    embedding_dimension = 8

    llm_client.embeddings = Mock()
    # evenly spaced embeddings for the knowledge base elements and specifically chosen embeddings for
    # each mock embedding calls.
    kb_embeddings = np.ones((4, embedding_dimension)) * np.arange(4)[:, None] / 100
    query_embeddings = np.ones((2, embedding_dimension)) * np.array([0.02, 10])[:, None]

    llm_client.embeddings.side_effect = [kb_embeddings]

    knowledge_base_df = make_knowledge_base_df()
    testset_generator = KnowledgeBaseTestsetGenerator(
        knowledge_base_df,
        model_name="Test model",
        model_description="This is a model for testing purpose.",
        llm_client=llm_client,
        context_neighbors=3,
    )
    testset_generator.rng = Mock()
    testset_generator.rng.choice = Mock()
    testset_generator.rng.choice.side_effect = list(query_embeddings)

    assert testset_generator.knowledge_base.index.d == 8
    assert testset_generator.knowledge_base.embeddings.shape == (4, 8)
    assert len(testset_generator.knowledge_base.documents) == 4
    assert testset_generator.knowledge_base.documents[2].page_content.startswith(
        "Scamorza is a Southern Italian cow's milk cheese."
    )

    test_set = testset_generator.generate_dataset(num_samples=2)
    assert len(test_set) == 2
    assert test_set.df.loc[0, "question"] == "Where is Camembert from?"
    assert test_set.df.loc[0, "reference_answer"] == "Camembert was created in Normandy, in the northwest of France."
    assert test_set.df.loc[0, "reference_context"] == CONTEXT_STRING
    assert test_set.df.loc[0, "difficulty_level"] == 1

    assert test_set.df.loc[1, "question"] == "Where is Camembert from?"
    assert test_set.df.loc[1, "reference_context"] == "\n------\n"
