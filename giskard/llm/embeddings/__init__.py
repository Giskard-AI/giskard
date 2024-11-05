from typing import Optional
from typing_extensions import deprecated

from ..client.litellm import LiteLLMClient
from .base import BaseEmbedding

_default_embedding = None
_default_embedding_model = "text-embedding-ada-002"


def get_embedding_model() -> str:
    return _default_embedding_model


def set_embedding_model(model: str):
    """
    Set the default embedding model to be used with litellm.

    Parameters
    ----------
    model : str
        Model name (e.g. 'text-embedding-ada-002' or 'text-embedding-3-large').
    """
    global _default_embedding_model
    _default_embedding_model = model


def get_default_embedding():
    """Get the default text embedding model.

    Returns
    -------
    BaseEmbedding
    """
    global _default_embedding

    _default_embedding = _default_embedding or LiteLLMClient(model=get_embedding_model())

    return _default_embedding


@deprecated(
    "set_default_embedding is deprecated, check documentation to setup llm: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html"
)
def set_default_embedding(embedding: Optional[BaseEmbedding] = None):
    """Set the default text embedding model.

    Parameters
    ----------
    embedding : BaseEmbedding
        Text embedding model.
    """
    global _default_embedding
    _default_embedding = embedding
