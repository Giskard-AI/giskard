from typing import Sequence, Union

import numpy as np
import torch

from .base import BaseEmbedding, batched


class OpenAIEmbedding(BaseEmbedding):
    def __init__(self, client, model, batch_size=20):
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed(self, texts: Sequence[str]) -> Union[np.ndarray, torch.Tensor]:
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for batch in batched(texts, self.batch_size):
            response = self.client.embeddings.create(input=batch, model=self.model)
            embeddings.extend([item.embedding for item in response.data])

        return embeddings
