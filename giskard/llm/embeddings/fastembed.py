from typing import Sequence

import numpy as np
from fastembed import TextEmbedding

from .base import BaseEmbedding


class FastEmbedEmbedding(BaseEmbedding):
    def __init__(self, text_embedding: TextEmbedding):
        """
        Parameters
        ----------
        text_embedding : TextEmbedding
            FastEmbed TextEmbedding model.
        """
        self.text_embedding = text_embedding

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        return np.array(list(self.text_embedding.embed(texts)))
