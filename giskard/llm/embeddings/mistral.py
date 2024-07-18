from typing import Sequence

import numpy as np

from .. import LLMImportError
from .base import BaseEmbedding

try:
    from mistralai.client import MistralClient
except ImportError as err:
    raise LLMImportError(
        flavor="llm", msg="To use Mistral models, please install the `mistralai` package with `pip install mistralai`"
    ) from err


class MistralEmbedding(BaseEmbedding):
    def __init__(self, client: MistralClient, model: str = "mistral-embed"):
        """
        Parameters
        ----------
        client : MistralClient
            Mistral client instance.
        model : str
            Model name.
        """
        self.model = model
        self.client = client

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        embeddings_batch_response = self.client.embeddings(
            model="mistral-embed",
            input=texts,
        )

        embeddings = []
        for data in embeddings_batch_response.data:
            embeddings.extend(data.embedding)

        return np.array(embeddings)
