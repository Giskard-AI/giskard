from typing import Optional

from ..client import get_default_llm_api
from .base import BaseEmbedding

_default_embedding = None


def get_default_embedding():
    """Get the default text embedding model.

    Returns
    -------
    BaseEmbedding
    """
    global _default_embedding

    if _default_embedding is not None:
        return _default_embedding

    # Try with OpenAI/AzureOpenAI if available
    try:
        from openai import AzureOpenAI, OpenAI

        from .openai import OpenAIEmbedding

        llm_api = get_default_llm_api()

        if llm_api == "azure":
            client = AzureOpenAI()
        else:
            client = OpenAI()

        _default_embedding = OpenAIEmbedding(client=client, model="text-embedding-ada-002")

        return _default_embedding
    except ImportError:
        pass

    # Try with local embeddings with FastEmbed
    try:
        from fastembed import TextEmbedding

        from .fastembed import FastEmbedEmbedding

        _default_embedding = FastEmbedEmbedding(
            text_embedding=TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        )
    except ImportError:
        pass

    raise ValueError(
        "Please setup `openai` or `fastembed` to use text embeddings, "
        "or set a custom embedding model using `giskard.llm.embeddings.set_default_embedding`."
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
