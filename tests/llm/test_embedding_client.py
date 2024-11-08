import os

import pydantic
import pytest

PYDANTIC_V2 = pydantic.__version__.startswith("2.")


@pytest.mark.skipif(not PYDANTIC_V2, reason="LiteLLM raise an error with pydantic < 2")
def test_get_embedding_model():
    from giskard.llm.embeddings import get_default_embedding, set_embedding_model
    from giskard.llm.embeddings.litellm import LiteLLMEmbedding

    set_embedding_model("mistral/mistral-embed")
    os.environ["OPENAI_API_KEY"] = "fake_api_key"

    embedding = get_default_embedding()
    assert isinstance(embedding, LiteLLMEmbedding)
    assert embedding.model == "mistral/mistral-embed"


@pytest.mark.skipif(not PYDANTIC_V2, reason="LiteLLM raise an error with pydantic < 2")
def test_get_embedding_model_fallback_openai():
    from giskard.llm.embeddings import get_default_embedding, set_embedding_model
    from giskard.llm.embeddings.litellm import LiteLLMEmbedding

    set_embedding_model(None)
    os.environ["OPENAI_API_KEY"] = "fake_api_key"

    embedding = get_default_embedding()
    assert isinstance(embedding, LiteLLMEmbedding)
    assert embedding.model == "text-embedding-3-small"


@pytest.mark.skipif(not PYDANTIC_V2, reason="LiteLLM raise an error with pydantic < 2")
def test_get_embedding_fallback_fastembed():
    from giskard.llm.embeddings import get_default_embedding, set_embedding_model
    from giskard.llm.embeddings.fastembed import FastEmbedEmbedding

    set_embedding_model(None)
    os.environ.pop("OPENAI_API_KEY", None)

    embedding = get_default_embedding()
    assert isinstance(embedding, FastEmbedEmbedding)
