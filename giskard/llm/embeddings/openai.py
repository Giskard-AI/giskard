from typing import Sequence

import numpy as np

from .base import BaseEmbedding, batched


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
