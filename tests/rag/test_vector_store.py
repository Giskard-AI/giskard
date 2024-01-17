from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from giskard.rag.vector_store import Document, VectorStore


def test_vector_store_creation():
    dimension = 8
    embeddings = np.repeat(np.arange(5)[:, None], 8, axis=1)
    documents = [Document({"feature": "This is a test string"})] * 5

    embedding_model = Mock()

    store = VectorStore(documents, embeddings, embedding_model)
    assert store.embeddings.shape == (5, 8)
    assert len(store.documents) == 5
    assert store.index.d == dimension
    assert store.index.ntotal == 5

    with pytest.raises(ValueError, match="Documents and embeddings must have the same length."):
        store = VectorStore(documents, np.repeat(np.arange(4)[:, None], 8, axis=1), embedding_model)

    with pytest.raises(ValueError, match="Documents and embeddings must contains at least one element."):
        store = VectorStore(documents, [], embedding_model)

    with pytest.raises(ValueError, match="Documents and embeddings must contains at least one element."):
        store = VectorStore([], [], embedding_model)


def test_vector_store_creation_from_df():
    dimension = 8
    df = pd.DataFrame(["This is a test string"] * 5)

    embedding_model = Mock()
    random_embedding = np.random.rand(dimension)
    embedding_model.embed_text.side_effect = [random_embedding] * 5

    store = VectorStore.from_df(df, embedding_model)
    assert store.index.d == dimension
    assert store.embeddings.shape == (5, 8)
    assert len(store.documents) == 5
    assert store.index.ntotal == 5

    assert np.allclose(store.embeddings[0], random_embedding)


def test_vector_store_similarity_search_with_score():
    dimension = 8
    embeddings = np.repeat(np.arange(100)[:, None], 8, axis=1)
    documents = [Document({"feature": f"This is test string {idx + 1}"}) for idx in range(100)]

    embedding_model = Mock()
    embedding_model.embed_text.side_effect = [np.ones(dimension) * 49]

    store = VectorStore(documents, embeddings, embedding_model)

    query = "This is test string 50"
    retrieved_elements = store.similarity_search_with_score(query, k=3)
    print([(ret.page_content, score) for (ret, score) in retrieved_elements])
    assert len(retrieved_elements) == 3
    assert retrieved_elements[0][0].page_content == "This is test string 50"
    assert retrieved_elements[0][1] == 0.0
    assert retrieved_elements[1][0].page_content == "This is test string 49"
    assert retrieved_elements[1][1] == 8.0
    assert retrieved_elements[2][0].page_content == "This is test string 51"
    assert retrieved_elements[2][1] == 8.0
