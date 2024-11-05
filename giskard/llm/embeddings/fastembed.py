from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence
from typing_extensions import deprecated

import numpy as np

from .base import BaseEmbedding

if TYPE_CHECKING:
    from fastembed import TextEmbedding


@deprecated(
    "FastEmbedEmbedding is deprecated, check documentation to setup llm: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html"
)
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


def try_get_fastembed_embeddings() -> Optional[FastEmbedEmbedding]:
    try:
        from fastembed import TextEmbedding

        from .fastembed import FastEmbedEmbedding

        return FastEmbedEmbedding(
            text_embedding=TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        )
    except ImportError:
        return None
