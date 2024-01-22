from typing import Sequence

from abc import ABC, abstractmethod

import numpy as np
from openai import OpenAI


class EmbeddingsBase(ABC):
    """Base class to build custom embedding models."""

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        ...

    @abstractmethod
    def embed_documents(self, documents: Sequence) -> np.ndarray:
        ...


class OpenAIEmbeddings(EmbeddingsBase):
    """Simple wrapper around the OpenAI embeddings API."""

    def __init__(self, model: str = "text-embedding-ada-002", client=None):
        self.model = model
        self._client = client if client is not None else OpenAI()

    def embed_text(self, text: str) -> np.ndarray:
        text = text.replace("\n", " ")
        try:
            out = self._client.embeddings.create(input=[text], model=self.model)
            embeddings = out.data[0].embedding
        except Exception as err:
            raise ValueError(f"Embedding creation failed for text: {text}.") from err
        return np.array(embeddings)

    def embed_documents(self, documents: Sequence) -> np.ndarray:
        text_batch = [doc.page_content.replace("\n", " ") for doc in documents]
        try:
            out = self._client.embeddings.create(input=text_batch, model=self.model)
            embeddings = [element.embedding for element in out.data]
        except Exception as err:
            raise ValueError("Batched embedding creation failed.") from err
        return np.stack(embeddings)
