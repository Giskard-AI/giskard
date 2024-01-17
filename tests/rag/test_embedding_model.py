from unittest.mock import Mock

import numpy as np

from giskard.rag import OpenAIEmbeddings


def test_openai_embeddings_model():
    embedding_mock = Mock()
    embedding_mock.embedding = np.ones(8)

    embedding_call = Mock()
    embedding_call.data = [embedding_mock]

    client = Mock()
    client.embeddings.create.side_effect = [embedding_call]

    embedding_model = OpenAIEmbeddings(client=client)

    embedded_text = embedding_model.embed_text("This a test string")
    assert len(embedded_text) == 8
    assert np.allclose(embedded_text, np.ones(8))
