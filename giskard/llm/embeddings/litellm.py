from typing import Sequence

import numpy as np

from ...utils.iterables import batched
from .. import LLMImportError
from .base import BaseEmbedding

try:
    import litellm
except ImportError as err:
    raise LLMImportError(flavor="litellm") from err


class LiteLLMEmbedding(BaseEmbedding):
    def __init__(self, model: str, batch_size=40):
        """
        Parameters
        ----------
        model : str
            Model name.
        batch_size : int, optional
            Batch size for embeddings, by default 40.
        """
        self.model = model
        self.batch_size = batch_size

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for batch in batched(texts, self.batch_size):
            response = litellm.embedding(model=self.model, input=batch)
            embeddings.extend([item.embedding for item in response.data])

        return np.array(embeddings)
