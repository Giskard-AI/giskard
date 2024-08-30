from typing import Optional, Sequence

import numpy as np

from ...utils.iterables import batched
from ..client import get_default_llm_api
from .base import BaseEmbedding

_default_embedding_model = "text-embedding-ada-002"


def get_embedding_model() -> str:
    return _default_embedding_model


def set_embedding_model(model: str):
    """
    Set the default embedding model to be used with OpenAI/AzureOpenAI client.

    Parameters
    ----------
    model : str
        Model name (e.g. 'text-embedding-ada-002' or 'text-embedding-3-large').
    """
    global _default_embedding_model
    _default_embedding_model = model


class OpenAIEmbedding(BaseEmbedding):
    def __init__(self, client, model: str, batch_size=40):
        """
        Parameters
        ----------
        client : OpenAI
            OpenAI or AzureOpenAI client instance.
        model : str
            Model name.
        batch_size : int, optional
            Batch size for embeddings, by default 40.
        """
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for batch in batched(texts, self.batch_size):
            response = self.client.embeddings.create(input=batch, model=self.model)
            embeddings.extend([item.embedding for item in response.data])

        return np.array(embeddings)


def try_get_openai_embeddings() -> Optional[OpenAIEmbedding]:
    try:
        from openai import AzureOpenAI, OpenAI

        from .openai import OpenAIEmbedding

        llm_api = get_default_llm_api()

        if llm_api == "azure":
            client = AzureOpenAI()
        else:
            client = OpenAI()

        return OpenAIEmbedding(client=client, model=get_embedding_model())
    except ImportError:
        return None
