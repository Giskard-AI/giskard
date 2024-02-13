from typing import Callable, Optional, Sequence

import numpy as np
import pandas as pd

from ..core.errors import GiskardInstallationError


class Document:
    """A class to wrap the elements of the knowledge base into a unified format."""

    def __init__(self, document: dict, features: Optional[Sequence] = None):
        features = features if features is not None else list(document.keys())

        if len(features) == 1:
            self.content = document[features[0]]
        else:
            self.content = "\n".join(f"{feat}: {document[feat]}" for feat in features)

        self.metadata = document


class VectorStore:
    """Stores all embedded Document of the knowledge base.
    Relies on `FlatIndexL2` class from FAISS.
    """

    def __init__(self, documents: Sequence[Document], embeddings: np.array, embedding_fn: Callable):
        if len(embeddings) == 0 or len(documents) == 0:
            raise ValueError("Documents and embeddings must contains at least one element.")
        if len(embeddings) != len(documents):
            raise ValueError("Documents and embeddings must have the same length.")

        try:
            from faiss import IndexFlatL2
        except ImportError as err:
            raise GiskardInstallationError(flavor="llm") from err

        self.embeddings = embeddings
        self.documents = documents
        self.embedding_fn = embedding_fn

        self.dimension = self.embeddings[0].shape[0]
        self.index = IndexFlatL2(self.dimension)
        self.index.add(self.embeddings)

    @classmethod
    def from_df(cls, df: pd.DataFrame, embedding_fn: Callable, features: Sequence[str] = None):
        if len(df) > 0:
            documents = [Document(knowledge_chunk, features=features) for knowledge_chunk in df.to_dict("records")]
            raw_texts = [d.content for d in documents]
            embeddings = embedding_fn(raw_texts).astype("float32")
            return cls(documents, embeddings, embedding_fn)
        else:
            raise ValueError("Cannot generate a vector store from empty DataFrame.")

    def similarity_search_with_score(self, query: Sequence[str], k: int) -> Sequence:
        query_emb = self.embedding_fn(query).astype("float32")
        return self.vector_similarity_search_with_score(query_emb, k)

    def vector_similarity_search_with_score(self, query_emb: np.ndarray, k: int) -> Sequence:
        query_emb = np.atleast_2d(query_emb)
        distances, indices = self.index.search(query_emb, k)
        return [(self.documents[i], d) for d, i in zip(distances[0], indices[0])]
