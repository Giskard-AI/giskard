from abc import ABC, abstractmethod

import numpy as np
from openai import OpenAI


class EmbeddingsBase(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> str:
        ...


class OpenAIEmbeddings(EmbeddingsBase):
    def __init__(self, model: str = "text-embedding-ada-002", client=None):
        self.model = model
        self._client = client if client is not None else OpenAI()

    def embed_text(self, text: str) -> str:
        text = text.replace("\n", " ")
        try:
            out = self._client.embeddings.create(input=[text], model=self.model)
            embeddings = out.data[0].embedding
        except Exception as err:
            raise ValueError(f"Embedding creation failed for text: {text}.") from err
        return np.array(embeddings)
