import os

from giskard.llm.embeddings import get_default_embedding, set_embedding_model
from giskard.llm.embeddings.fastembed import FastEmbedEmbedding
from giskard.llm.embeddings.litellm import LiteLLMEmbedding


def test_get_embedding_model():
    set_embedding_model("mistral/mistral-embed")
    os.environ["OPENAI_API_KEY"] = "fake_api_key"

    embedding = get_default_embedding()
    assert isinstance(embedding, LiteLLMEmbedding)
    assert embedding.model == "mistral/mistral-embed"


def test_get_embedding_model_fallback_openai():
    set_embedding_model(None)
    os.environ["OPENAI_API_KEY"] = "fake_api_key"

    embedding = get_default_embedding()
    assert isinstance(embedding, LiteLLMEmbedding)
    assert embedding.model == "text-embedding-3-small"


def test_get_embedding_fallback_fastembed():
    set_embedding_model(None)
    os.environ.pop("OPENAI_API_KEY", None)

    embedding = get_default_embedding()
    assert isinstance(embedding, FastEmbedEmbedding)
