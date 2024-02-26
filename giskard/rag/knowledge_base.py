from typing import Callable, Optional, Sequence

import logging

import numpy as np
import pandas as pd

from ..core.errors import GiskardInstallationError
from ..llm.client import LLMClient, get_default_client

logger = logging.getLogger(__name__)


class Document:
    """A class to wrap the elements of the knowledge base into a unified format."""

    def __init__(self, document: dict, features: Optional[Sequence] = None):
        features = features if features is not None else list(document.keys())

        if len(features) == 1:
            self.content = document[features[0]]
        else:
            self.content = "\n".join(f"{feat}: {document[feat]}" for feat in features)

        self.metadata = document


class KnowledgeBase:
    def __init__(
        self,
        documents: Sequence[Document],
        embeddings: np.array,
        embedding_fn: Callable,
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        seed: int = 1729,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        if len(embeddings) == 0 or len(documents) == 0:
            raise ValueError("Documents and embeddings must contains at least one element.")
        if len(embeddings) != len(documents):
            raise ValueError("Documents and embeddings must have the same length.")

        try:
            from faiss import IndexFlatL2
        except ImportError as err:
            raise GiskardInstallationError(flavor="llm") from err

        self._documents = documents
        self._embeddings = embeddings
        self._context_similarity_threshold = context_similarity_threshold
        self._context_neighbors = context_neighbors

        self._llm_client = llm_client or get_default_client()
        self._topics_inst = None
        self._vector_store_inst = None
        self._embedding_fn = embedding_fn
        self._rng = np.random.default_rng(seed=seed)

        self._dimension = self._embeddings[0].shape[0]
        self._index = IndexFlatL2(self._dimension)
        self._index.add(self._embeddings)

    @property
    def topics(self):
        if self._topics_inst is None:
            self._topics_inst = self._find_topics()
        return self._topics_inst

    # def _find_topics(self):
    #     embeddings_tsne = tsne.fit_transform(self._embeddings)
    #     dbscan = HDBSCAN(eps=0.1, min_samples=2, metric='cosine')
    #     clustering = dbscan.fit(self._embeddings)

    def _get_random_document(self):
        return self._rng.choice(self._documents)

    def _get_random_document_group(self):
        seed_embedding = self._rng.choice(self._embeddings)
        relevant_documents = [
            document
            for (document, score) in self.vector_similarity_search_with_score(seed_embedding, k=self._context_neighbors)
            if score < self._context_similarity_threshold
        ]

        return relevant_documents

    @classmethod
    def from_df(
        cls,
        df: pd.DataFrame,
        embedding_model: Optional[str] = "text-embedding-ada-002",
        knowledge_base_columns: Sequence[str] = None,
        llm_client: Optional[LLMClient] = None,
        **kwargs,
    ):
        llm_client = llm_client or get_default_client()

        def embedding_fn(query):
            return llm_client.embeddings(query, model=embedding_model)

        if len(df) > 0:
            documents = [
                Document(knowledge_chunk, features=knowledge_base_columns) for knowledge_chunk in df.to_dict("records")
            ]
            raw_texts = [d.content for d in documents]
            embeddings = embedding_fn(raw_texts).astype("float32")
            return cls(documents, embeddings, embedding_fn, llm_client=llm_client, **kwargs)
        else:
            raise ValueError("Cannot generate a vector store from empty DataFrame.")

    def similarity_search_with_score(self, query: Sequence[str], k: int) -> Sequence:
        query_emb = self._embedding_fn(query).astype("float32")
        return self.vector_similarity_search_with_score(query_emb, k)

    def vector_similarity_search_with_score(self, query_emb: np.ndarray, k: int) -> Sequence:
        query_emb = np.atleast_2d(query_emb)
        distances, indices = self._index.search(query_emb, k)
        return [(self._documents[i], d) for d, i in zip(distances[0], indices[0])]
