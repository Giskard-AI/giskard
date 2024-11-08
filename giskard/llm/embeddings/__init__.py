from typing import Optional
from typing_extensions import deprecated

import logging
import os

from .base import BaseEmbedding
from .fastembed import try_get_fastembed_embeddings

logger = logging.getLogger(__name__)

_default_embedding = None

_default_embedding_model: Optional[str] = None
_default_embedding_params = dict()


def get_embedding_model() -> Optional[str]:
    global _default_embedding_model

    if _default_embedding_model is not None:
        return _default_embedding_model

    if "OPENAI_API_KEY" in os.environ:
        _default_embedding_model = "text-embedding-3-small"
        logger.info(
            f"No embedding model set though giskard.llm.set_embedding_model. Defaulting to openai/{_default_embedding_model} since OPENAI_API_KEY is set."
        )
        return _default_embedding_model


def set_embedding_model(model: str, **kwargs):
    """
    Set the default embedding model to be used with litellm.

    Parameters
    ----------
    model : str
        Model name (e.g. 'text-embedding-ada-002' or 'text-embedding-3-large').
    """
    global _default_embedding_model
    global _default_embedding_params
    global _default_embedding

    _default_embedding_model = model
    _default_embedding_params = kwargs
    _default_embedding = None


def get_default_embedding():
    """Get the default text embedding model.

    Returns
    -------
    BaseEmbedding
    """
    global _default_embedding

    model = get_embedding_model()

    if model is None:
        _default_embedding = try_get_fastembed_embeddings()

        if _default_embedding is None:
            raise ValueError(
                "No embeddings model set. Please check documentation to setup an embedding model: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html"
            )

        logger.info("No embedding model set though giskard.llm.set_embedding_model. Defaulting to fastembed.")
        return _default_embedding

    try:
        from .litellm import LiteLLMEmbedding

        _default_embedding = _default_embedding or LiteLLMEmbedding(
            model=model, embedding_params=_default_embedding_params
        )

        return _default_embedding
    except ImportError:
        raise ValueError(f"LLM scan using {_default_embedding_model} requires litellm")


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
