from typing import Optional

from .base import BaseEmbedding
from .fastembed import try_get_fastembed_embeddings
from .openai import try_get_openai_embeddings

_default_embedding = None


def get_default_embedding():
    """Get the default text embedding model.

    Returns
    -------
    BaseEmbedding
    """
    global _default_embedding

    _default_embedding = _default_embedding or try_get_openai_embeddings() or try_get_fastembed_embeddings()

    if _default_embedding is None:
        raise ValueError(
            "Please setup `openai` or `fastembed` to use text embeddings, "
            "or set a custom embedding model using `giskard.llm.embeddings.set_default_embedding`."
        )

    return _default_embedding


def set_default_embedding(embedding: Optional[BaseEmbedding] = None):
    """Set the default text embedding model.

    Parameters
    ----------
    embedding : BaseEmbedding
        Text embedding model.
    """
    global _default_embedding
    _default_embedding = embedding
