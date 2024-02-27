from typing import Callable, Optional, Sequence

import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN
from sklearn.manifold import TSNE

from ..core.errors import GiskardInstallationError
from ..llm.client import LLMClient, LLMMessage, get_default_client

logger = logging.getLogger(__name__)


TOPIC_SUMMARIZATION_PROMPT = """You are a superpowerful summarization AI model. 

Your task is to summarize a list of paragraphs and extract the topic in common to ALL paragraphs.
- Your answer must be 3 to 5 words at most.
- The summary must be written in {language}.

All the information about the topic is delimited with  <topic></topic> tags.
The paragraphs will be separated with "----------".
Here is the list of paragraphs:
<topic>
{topics_elements}
</topic>

Make sure to only return the summary as a valid string, starting and ending with quotes."""


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
        language: str = "en",
        context_neighbors: int = 4,
        context_similarity_threshold: float = 0.2,
        seed: int = 1729,
        llm_client: Optional[LLMClient] = None,
        cluster_size: int = 2,
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
        self._language = language

        self._llm_client = llm_client or get_default_client()
        self._topics_inst = None
        self._vector_store_inst = None
        self._embedding_fn = embedding_fn
        self._rng = np.random.default_rng(seed=seed)
        self._cluster_size = cluster_size

        self._dimension = self._embeddings[0].shape[0]
        self._index = IndexFlatL2(self._dimension)
        self._index.add(self._embeddings)

    @property
    def topics(self):
        if self._topics_inst is None:
            self._topics_inst = self._find_topics()
        return self._topics_inst

    def _find_topics(self):
        dbscan = HDBSCAN(min_cluster_size=self._cluster_size, metric="euclidean", cluster_selection_epsilon=0.1)
        clustering = dbscan.fit(self._embeddings)
        for i, doc in enumerate(self._documents):
            doc.topic_id = clustering.labels_[i]

        topics_ids = set(clustering.labels_)
        topics = {
            idx: self._get_topic_name([self._documents[doc_id] for doc_id in np.where(clustering.labels_ == idx)[0]])
            for idx in topics_ids
            if idx != -1
        }
        topics[-1] = "Others"
        return topics

    def _get_topic_name(self, topic_documents):
        self._rng.shuffle(topic_documents)
        topics_str = "\n\n".join(["----------" + doc.content for doc in topic_documents])

        # prevent context window overflow
        topics_str = topics_str[: 3 * 8192]
        prompt = TOPIC_SUMMARIZATION_PROMPT.format(language=self._language, topics_elements=topics_str)

        return self._llm_client.complete([LLMMessage(role="user", content=prompt)]).content[1:-1]

    def plot_topics(self):
        if self.topics is None:
            raise ValueError("No topics found.")
        tsne = TSNE(perplexity=5)
        embeddings_tsne = tsne.fit_transform(self._embeddings)

        fig, ax = plt.subplots()

        legend_handles = []
        legend_labels = []

        edge_cmap = {
            topic_id: (*plt.cm.tab20b(topic_id)[:3], 1.0) if topic_id >= 0 else (0.4, 0.4, 0.4, 1.0)
            for topic_id in self.topics
        }
        face_cmap = {
            topic_id: (*plt.cm.tab20b(topic_id)[:3], 0.7) if topic_id >= 0 else (0.4, 0.4, 0.4, 0.7)
            for topic_id in self.topics
        }

        for topic_id, topic in self.topics.items():
            legend_handles.append(
                matplotlib.lines.Line2D(
                    [],
                    [],
                    color="white",
                    marker="o",
                    markeredgecolor=edge_cmap[topic_id],
                    markerfacecolor=face_cmap[topic_id],
                    markeredgewidth=1.5,
                    markersize=10,
                )
            )
            legend_labels.append(topic)

        ax.scatter(
            embeddings_tsne[:, 0],
            embeddings_tsne[:, 1],
            color=[face_cmap[doc.topic_id] for doc in self._documents],
            edgecolor=[edge_cmap[doc.topic_id] for doc in self._documents],
            linewidth=1.5,
            s=75,
        )
        for i in range(embeddings_tsne.shape[0]):
            ax.annotate(i, (embeddings_tsne[:, 0][i] - 1, embeddings_tsne[:, 1][i] - 1))
        legend = ax.legend(legend_handles, legend_labels, loc=(1.1, 0), title="Topics")
        legend.get_title().set_fontsize("14")

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
