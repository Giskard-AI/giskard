from unittest.mock import Mock

import numpy as np
import pandas as pd

from giskard.rag.knowledge_base import KnowledgeBase


def test_knowledge_base_creation_from_df():
    dimension = 8
    df = pd.DataFrame(["This is a test string"] * 5)

    llm_client = Mock()
    llm_client.embeddings = Mock()
    random_embedding = np.random.rand(5, dimension)
    llm_client.embeddings.side_effect = [random_embedding]

    knowledge_base = KnowledgeBase(df, llm_client=llm_client)
    assert knowledge_base._index.d == dimension
    assert knowledge_base._embeddings.shape == (5, 8)
    assert len(knowledge_base._documents) == 5
    assert knowledge_base._index.ntotal == 5

    assert np.allclose(knowledge_base._embeddings, random_embedding)


def test_knowledge_base_similarity_search_with_score():
    dimension = 8

    df = pd.DataFrame([f"This is test string {idx + 1}" for idx in range(100)])

    llm_client = Mock()
    llm_client.embeddings = Mock()
    llm_client.embeddings.side_effect = [np.ones((1, dimension)) * 49] + [np.repeat(np.arange(100)[:, None], 8, axis=1)]

    knowledge_base = KnowledgeBase(df, llm_client=llm_client)

    query = ["This is test string 50"]
    retrieved_elements = knowledge_base.similarity_search_with_score(query, k=3)
    assert len(retrieved_elements) == 3
    assert retrieved_elements[0][0].content == "This is test string 50"
    assert retrieved_elements[0][1] == 0.0
    assert retrieved_elements[1][0].content == "This is test string 49"
    assert retrieved_elements[1][1] == 8.0
    assert retrieved_elements[2][0].content == "This is test string 51"
    assert retrieved_elements[2][1] == 8.0
