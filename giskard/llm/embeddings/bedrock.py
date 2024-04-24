from typing import Sequence

import json

import numpy as np

from .base import BaseEmbedding


class BedrockEmbedding(BaseEmbedding):
    def __init__(self, client, model: str):
        """
        Parameters
        ----------
        client : Bedrock
            boto3 based Bedrock runtime client instance.
        model : str
            Model name.
        """
        self.model = model
        self.client = client

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if "titan" not in self.model:
            raise ValueError(f"Only titan embedding models are supported currently, got {self.model} instead")

        if isinstance(texts, str):
            texts = [texts]

        accept = "application/json"
        contentType = "application/json"
        embeddings = []
        for text in texts:
            body = json.dumps({"inputText": text})
            response = self.client.invoke_model(body=body, modelId=self.model, accept=accept, contentType=contentType)
            response_body = json.loads(response.get("body").read())
            embedding = response_body.get("embedding")
            embeddings.append(embedding)

        return np.array(embeddings)
