from typing import Dict, Optional, Sequence

import logging
import uuid

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

from ..llm.client import ChatMessage, LLMClient, get_default_client
from ..llm.embeddings import get_default_embedding
from ..llm.embeddings.base import BaseEmbedding
from ..llm.errors import LLMImportError
from ..utils.analytics_collector import analytics
from ..utils.language_detection import detect_lang
from .knowledge_base_plots import get_failure_plot, get_knowledge_plot

try:
    import umap
    from bokeh.io import output_notebook, reset_output, show
except ImportError as err:
    raise LLMImportError(flavor="llm") from err


logger = logging.getLogger("giskard.rag")

LANGDETECT_MAX_TEXT_LENGTH = 300
LANGDETECT_DOCUMENTS = 10

TOPIC_SUMMARIZATION_PROMPT = """Your task is to define the topic which best represents a set of documents.

Your are given below a list of documents and you must extract the topic best representing ALL contents.
- The topic name should be between 1 to 5 words
- Provide the topic in this language: {language}

Make sure to only return the topic name between quotes, and nothing else.

For example, given these documents:

<documents>
Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.
----------
Bleu d'Auvergne is a French blue cheese, named for its place of origin in the Auvergne region.
----------
Roquefort is a sheep milk cheese from the south of France.
</documents>

The topic is:
"French Cheese"

Now it's your turn. Here is the list of documents:

<documents>
{topics_elements}
</documents>

The topic is:
"""


class Document:
    """A class to wrap the elements of the knowledge base into a unified format."""

    def __init__(
        self, document: Dict[str, str], doc_id: str = None, features: Optional[Sequence] = None, topic_id: int = None
    ):
        features = features if features is not None else list(document.keys())

        self.content = (
            "\n".join(f"{k}: {v}" for k, v in document.items() if k in features)
            if len(features) > 1
            else document[features[0]]
        )

        self.metadata = document
        self.id = doc_id if doc_id is not None else str(uuid.uuid4())
        self.embeddings = None
        self.reduced_embeddings = None
        self.topic_id = topic_id


class KnowledgeBase:
    """
    A class to handle the knowledge base and the associated vector store.

    Parameters
    ----------
    knowledge_base_df: pd.DataFrame
        A dataframe containing the whole knowledge base.
    columns: Sequence[str], optional
        The list of columns from the `knowledge_base` to consider. If not specified, all columns of the knowledge base
        dataframe will be concatenated to produce a single document.
        Example: if your knowledge base consists in FAQ data with columns "Q" and "A", we will format each row into a
        single document "Q: [question]\\nA: [answer]" to generate questions.
    seed: int, optional
        The seed to use for random number generation.
    llm_client: LLMClient, optional:
        The LLM client to use for question generation. If not specified, a default openai client will be used.
    embedding_model: BaseEmbedding, optional
        The giskard embedding model to use for the knowledge base. By default we use giskard default model which is OpenAI "text-embedding-ada-002".
    min_topic_size: int, optional
        The minimum number of document to form a topic inside the knowledge base.
    chunk_size: int = 2048
        The number of document to embed in a single batch.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        columns: Optional[Sequence[str]] = None,
        seed: int = None,
        llm_client: Optional[LLMClient] = None,
        embedding_model: Optional[BaseEmbedding] = None,
        min_topic_size: Optional[int] = None,
        chunk_size: int = 2048,
    ) -> None:
        if len(data) == 0:
            raise ValueError("Cannot generate a Knowledge Base from empty DataFrame.")

        self._documents = [
            Document(
                knowledge_chunk,
                features=columns,
                doc_id=doc_id,
            )
            for doc_id, knowledge_chunk in data.to_dict("index").items()
        ]

        self._documents = [doc for doc in self._documents if doc.content.strip() != ""]

        if len(self) == 0:
            raise ValueError("Cannot generate a Knowledge Base with empty documents.")

        self._knowledge_base_df = data
        self._columns = columns

        self._rng = np.random.default_rng(seed=seed)
        self._llm_client = llm_client or get_default_client()
        self._embedding_model = embedding_model or get_default_embedding()

        # Estimate the minimum number of documents to form a topic
        self._min_topic_size = min_topic_size or round(2 + np.log(len(self._documents)))
        self.chunk_size = chunk_size

        self._embeddings_inst = None
        self._topics_inst = None
        self._index_inst = None
        self._reduced_embeddings_inst = None

        # Detect language of the documents, use only the first characters of a few documents to speed up the process
        document_languages = [
            detect_lang(doc.content[:LANGDETECT_MAX_TEXT_LENGTH])
            for doc in self._rng.choice(self._documents, size=LANGDETECT_DOCUMENTS)
        ]
        languages, occurences = np.unique(
            ["en" if (pd.isna(lang) or lang == "unknown") else lang for lang in document_languages], return_counts=True
        )
        self._language = languages[np.argmax(occurences)]

        self._documents_index = {doc.id: doc for doc in self._documents}

        analytics.track(
            "raget:knowledge-base-creation",
            {
                "num_documents": len(self._documents),
                "language": self._language,
            },
        )

    @classmethod
    def from_pandas(cls, df: pd.DataFrame, columns: Optional[Sequence[str]] = None, **kwargs) -> "KnowledgeBase":
        """Create a KnowledgeBase from a pandas DataFrame.

        Parameters
        ----------
        df: pd.DataFrame
            The DataFrame containing the knowledge base.
        columns: Sequence[str], optional
            The list of columns from the `knowledge_base` to consider. If not specified, all columns of the knowledge base
            dataframe will be concatenated to produce a single document.
            Example: if your knowledge base consists in FAQ data with columns "Q" and "A", we will format each row into a
            single document "Q: [question]\\nA: [answer]" to generate questions.
        kwargs:
            Additional settings for knowledge base (see __init__).
        """
        return cls(data=df, columns=columns, **kwargs)

    @property
    def _embeddings(self):
        if self._embeddings_inst is None:
            logger.debug("Computing Knowledge Base embeddings.")
            self._embeddings_inst = np.array(self._embedding_model.embed([doc.content for doc in self._documents]))
            for doc, emb in zip(self._documents, self._embeddings_inst):
                doc.embeddings = emb
        return self._embeddings_inst

    @property
    def _reduced_embeddings(self):
        if self._reduced_embeddings_inst is None:
            logger.debug("Calculating UMAP projection")
            reducer = umap.UMAP(
                n_neighbors=50,
                min_dist=0.5,
                n_components=2,
                random_state=1234,
                n_jobs=1,
            )
            self._reduced_embeddings_inst = reducer.fit_transform(self._embeddings)
            for doc, emb in zip(self._documents, self._reduced_embeddings_inst):
                doc.reduced_embeddings = emb
        return self._reduced_embeddings_inst

    @property
    def _dimension(self):
        return self._embeddings[0].shape[0]

    def get_savable_data(self):
        return {
            "columns": self._columns,
            "min_topic_size": self._min_topic_size,
            "topics": {int(k): topic for k, topic in self.topics.items()},
            "documents_topics": [int(doc.topic_id) for doc in self._documents],
        }

    @property
    def _index(self):
        if self._index_inst is None:
            try:
                from faiss import IndexFlatL2
            except ImportError as err:
                raise LLMImportError(flavor="llm") from err

            self._index_inst = IndexFlatL2(self._dimension)
            self._index_inst.add(self._embeddings)
        return self._index_inst

    @property
    def topics(self):
        if self._topics_inst is None:
            self._topics_inst = self._find_topics()
        return self._topics_inst

    def _find_topics(self):
        logger.info("Finding topics in the knowledge base.")
        hdbscan = HDBSCAN(
            min_cluster_size=self._min_topic_size,
            min_samples=3,
            metric="euclidean",
            cluster_selection_epsilon=0.0,
        )
        clustering = hdbscan.fit(self._reduced_embeddings)

        for i, doc in enumerate(self._documents):
            doc.topic_id = clustering.labels_[i]

        topics_ids = set(clustering.labels_)
        topics = {
            idx: self._get_topic_name([self._documents[doc_id] for doc_id in np.nonzero(clustering.labels_ == idx)[0]])
            for idx in topics_ids
            if idx != -1
        }
        topics[-1] = "Others"

        analytics.track(
            "raget:knowledge-topic-creation",
            {
                "num_topic": len(topics),
                "min_topic_size": self._min_topic_size,
            },
        )
        logger.info(f"Found {len(topics)} topics in the knowledge base.")
        return topics

    def _get_topic_name(self, topic_documents):
        logger.debug("Create topic name from topic documents")
        self._rng.shuffle(topic_documents)
        topics_str = "\n\n".join(["----------" + doc.content[:500] for doc in topic_documents[:10]])

        # prevent context window overflow
        topics_str = topics_str[: 3 * 8192]
        prompt = TOPIC_SUMMARIZATION_PROMPT.format(language=self._language, topics_elements=topics_str)

        raw_output = self._llm_client.complete([ChatMessage(role="user", content=prompt)], temperature=0.0).content

        return raw_output.strip().strip('"')

    def plot_topics(self, notebook: bool = True):
        if notebook:
            output_notebook()
        else:
            reset_output()
        show(get_knowledge_plot(self))

    def get_knowledge_plot(self):
        return get_knowledge_plot(self)

    def get_failure_plot(self, question_evaluation: Sequence[dict] = None):
        return get_failure_plot(self, question_evaluation)

    def get_random_document(self):
        return self._rng.choice(self._documents)

    def get_neighbors(self, seed_document: Document, n_neighbors: int = 4, similarity_threshold: float = 0.2):
        seed_embedding = seed_document.embeddings

        relevant_documents = [
            doc
            for (doc, score) in self.vector_similarity_search_with_score(seed_embedding, k=n_neighbors)
            if score < similarity_threshold
        ]

        return relevant_documents

    def similarity_search_with_score(self, query: str, k: int) -> Sequence:
        query_emb = np.array(self._embedding_model.embed(query), dtype="float32")
        return self.vector_similarity_search_with_score(query_emb, k)

    def vector_similarity_search_with_score(self, query_emb: np.ndarray, k: int) -> Sequence:
        query_emb = np.atleast_2d(query_emb)
        distances, indices = self._index.search(query_emb, k)
        return [(self._documents[i], d) for d, i in zip(distances[0], indices[0])]

    def __len__(self):
        return len(self._documents)

    def __getitem__(self, doc_id: str):
        return self._documents_index[doc_id]
