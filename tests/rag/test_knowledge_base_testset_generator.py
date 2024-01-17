from unittest.mock import Mock

import numpy as np
import pandas as pd

from giskard.llm.client import LLMFunctionCall, LLMOutput
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


CONTEXT_STRING = """### Context 1 ###
Scamorza is a Southern Italian cow's milk cheese.
######

### Context 2 ###
Bleu d'Auvergne is a French blue cheese, named for its place of origin in the Auvergne region.
######

### Context 3 ###
Freeriding is a style of snowboarding or skiing performed on natural, un-groomed terrain, without a set course, goals or rules.
######"""


def test_testset_generation():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {"question": "Where is Camembert from?"},
                    ]
                },
            ),
        ),
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {"answer": "Camembert was created in Normandy, in the northwest of France."},
                    ]
                },
            ),
        ),
    ] * 2

    embedding_dimension = 8

    embedding_model = Mock()
    # evenly spaced embeddings for the knowledge base elements and specifically chosen embeddings for
    # each mock embedding calls.
    embedding_model.embed_text.side_effect = [np.ones(embedding_dimension) * idx / 100 for idx in range(4)] + [
        np.ones(8) * 0.02,
        np.ones(8) * 10,
    ]

    knowledge_base_df = make_knowledge_base_df()
    testset_generator = KnowledgeBaseTestsetGenerator(
        knowledge_base_df,
        model_name="Test model",
        model_description="This is a model for testing purpose.",
        llm_client=llm_client,
        embedding_model=embedding_model,
        context_neighbors=3,
    )

    assert testset_generator.knowledge_base.index.d == 8
    assert testset_generator.knowledge_base.embeddings.shape == (4, 8)
    assert len(testset_generator.knowledge_base.documents) == 4
    assert testset_generator.knowledge_base.documents[2].page_content.startswith(
        "Scamorza is a Southern Italian cow's milk cheese."
    )

    test_set = testset_generator.generate_testset(num_samples=2)
    assert len(test_set) == 2
    assert test_set.loc[0, "question"] == "Where is Camembert from?"
    assert test_set.loc[0, "reference_answer"] == "Camembert was created in Normandy, in the northwest of France."
    assert test_set.loc[0, "reference_context"] == CONTEXT_STRING
    assert test_set.loc[0, "difficulty_level"] == 1

    assert test_set.loc[1, "question"] == "Where is Camembert from?"
    assert test_set.loc[1, "reference_context"] == ""
