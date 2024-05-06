from typing import Sequence

import numpy as np

from .base import BaseEmbedding


class LangchainEmbeddings(BaseEmbedding):
    def __init__(self, embeddings):
        """
        Parameters
        ----------
        embeddings : Embeddings
            langchain embeddings
        """
        self.embeddings = embeddings

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        return np.array(self.embeddings.embed_documents(texts))
