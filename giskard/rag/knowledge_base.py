from pathlib import Path
import pickle
from typing import Dict, Optional, Sequence

import logging
import uuid

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

import tempfile
import os
import json
from huggingface_hub import DatasetCard, HfApi, HfFolder, upload_file, hf_hub_download

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

    # file names to save and load the knowledge base
    _saving_filenames = [
        "knowledge_base.parquet", 
        "embeddings.npy", 
        "reduced_embeddings.npy", 
        "config.json", 
        "llm_client.pkl", 
        "embedding_model.pkl"
    ]

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

        self.seed = seed
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
        self._config_inst = None

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

    def save(self, dirpath: str):
        """Save the KnowledgeBase to a directory.

        Parameters
        ----------
        dirpath : str
            The directory path where the KnowledgeBase will be saved.
        """
        os.makedirs(dirpath, exist_ok=True)

        # save raw data
        self._knowledge_base_df.to_parquet(os.path.join(dirpath, "knowledge_base.parquet"))
    
        # save embeddings
        if self._embeddings_inst is not None:
            np.save(os.path.join(dirpath, "embeddings.npy"), self._embeddings_inst)
        if self._reduced_embeddings_inst is not None:
            np.save(os.path.join(dirpath, "reduced_embeddings.npy"), self._reduced_embeddings_inst)
        
        # save llm and embedding objects
        with open(os.path.join(dirpath, "llm_client.pkl"), "wb") as f:
            pickle.dump(self._llm_client, f)
        with open(os.path.join(dirpath, "embedding_model.pkl"), "wb") as f:
            pickle.dump(self._embedding_model, f)

        # save config
        with open(os.path.join(dirpath, "config.json"), "w") as f:
            json.dump(self._config, f, indent=2)
        
        logger.info("KnowledgeBase saved successfully.")

    @classmethod
    def load(cls, dirpath: str, llm_client: Optional[LLMClient] = None,
        embedding_model: Optional[BaseEmbedding] = None) -> "KnowledgeBase":
        """
        Load a KnowledgeBase instance from a specified directory.

        Parameters
        ----------
        dirpath : str
            The path to the directory containing the saved KnowledgeBase data.
        llm_client : LLMClient, optional
            An optional LLMClient instance. If not provided, it will be loaded from the directory.
        embedding_model : BaseEmbedding, optional
            An optional embedding model instance. If not provided, it will be loaded from the directory.

        Returns
        -------
        KnowledgeBase
            An instance of the KnowledgeBase class loaded with the data, configuration, and models from the specified directory.

        Raises
        ------
        ValueError
            If the specified directory does not exist or the required "knowledge_base.parquet" file is missing.

        Notes
        -----
        The directory must contain the following files:
        - "knowledge_base.parquet": The raw data for the KnowledgeBase.

        Optional files:
        - "llm_client.pkl": A serialized LLMClient object (if llm_client is not provided).
        - "embedding_model.pkl": A serialized embedding model object (if embedding_model is not provided).
        - "config.json": A JSON file containing configuration parameters.
        - "embeddings.npy": A NumPy file containing precomputed embeddings.
        - "reduced_embeddings.npy": A NumPy file containing reduced embeddings.

        Missing optional files will result in warnings, and the KnowledgeBase will be created without those components.
        """
        
        dirpath = Path(dirpath)
        if not dirpath.exists():
            raise ValueError(f"Cannot load the KnowledgeBase. Directory {dirpath} does not exist.")
        
        filepaths = {}
        for filename in cls._saving_filenames:
            key = filename.split('.')[0] + "_filepath"
            try:
                fp = dirpath / filename
                assert fp.exists(), f"File {filename} not found in {dirpath}."
                filepaths[key] = str(fp)
            except Exception as e:
                logger.warning(str(e))
                if filename == "knowledge_base.parquet":
                    raise ValueError("Cannot load the KnowledgeBase. Could not find knowledge_base.parquet file.")
                filepaths[key] = None

        return cls._load(**filepaths, llm_client=llm_client, embedding_model=embedding_model)

    def push_to_hf_hub(self, repo_id: str, hf_token: Optional[str] = None, private: bool = False):
        """
        Push the KnowledgeBase to the Hugging Face Hub.

        Parameters
        ----------
        repo_id : str
            The repo ID on Hugging Face Hub (e.g., "org-name/my-knowledge-base").
        hf_token : str, optional
            Hugging Face token for authentication. If None, will use local token.
        private : bool
            Whether to make the repo private or public.
        """

        api = HfApi(token=hf_token or HfFolder.get_token())
        api.create_repo(repo_id, repo_type="dataset", private=private, exist_ok=True)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:

                self.save(tmpdir)
                
                # push the files to the hub
                for filename in self._saving_filenames:
                    filepath = os.path.join(tmpdir, filename)
                    if os.path.exists(filepath):
                        upload_file(
                            path_or_fileobj=filepath,
                            path_in_repo=filename,
                            repo_id=repo_id,
                            repo_type="dataset",
                            token=hf_token,
                        )
            logger.info(f"KnowledgeBase pushed to https://huggingface.co/datasets/{repo_id}")

            # Load the dataset card template
            template_path = Path(__file__).parent / "knowledge_base_card_template.md"
            template = template_path.read_text()

            # Make and push the dataset card
            content = template.format(repo_id=repo_id, num_items=len(self._knowledge_base_df), config=json.dumps(self._config_inst, indent=4))
            return DatasetCard(content=content).push_to_hub(repo_id=repo_id, token=hf_token, repo_type="dataset")
        
        except Exception as e:
            logger.error(f"Error pushing to Hugging Face Hub: {e}")

    @classmethod
    def _load(cls, 
            config_filepath: str, 
            knowledge_base_filepath: str, 
            llm_client_filepath: str, 
            embedding_model_filepath: str, 
            embeddings_filepath: str, 
            reduced_embeddings_filepath: str, 
            llm_client: Optional[LLMClient] = None,
            embedding_model: Optional[BaseEmbedding] = None) -> "KnowledgeBase":
        """
        Load a KnowledgeBase instance by loading data from specified file paths.

        This method initializes a KnowledgeBase object using the provided file paths for configuration, data, 
        embeddings, and models. It handles loading and deserialization of the necessary components, such as 
        the knowledge base data, LLM client, embedding model, and precomputed embeddings.

        Parameters
        ----------
        config_filepath : str
            Path to the JSON file containing the KnowledgeBase configuration.
        knowledge_base_filepath : str
            Path to the Parquet file containing the knowledge base data.
        llm_filepath : str
            Path to the pickle file containing the serialized LLM client.
        embedding_model_filepath : str
            Path to the pickle file containing the serialized embedding model.
        embeddings_filepath : str
            Path to the NumPy file containing precomputed embeddings.
        reduced_embeddings_filepath : str
            Path to the NumPy file containing reduced embeddings.
        llm_client : LLMClient, optional
            An optional LLMClient instance. If not provided, it will be loaded from the specified file path.
        embedding_model : BaseEmbedding, optional
            An optional embedding model instance. If not provided, it will be loaded from the specified file path.

        Returns
        -------
        KnowledgeBase
            An instance of the KnowledgeBase class loaded with the data, configuration, and models.

        Notes
        -----
        - If any of the optional file paths (e.g., embeddings or reduced embeddings) are missing or fail to load, 
          warnings will be logged, and the KnowledgeBase will still be created without those components.
        - Default values will be used for missing configuration parameters or models if they cannot be loaded.
        """

        data = pd.read_parquet(knowledge_base_filepath)

        config = {}
        if config_filepath:
            try:
                config = json.loads(open(config_filepath, "r").read())
            except Exception as e:
                logger.warning(f"Could not load config: {e}. Using default values.")
        
        llm_client = None
        if not llm_client and llm_client_filepath:
            try:
                llm_client = pickle.load(open(llm_client_filepath, "rb"))
            except Exception as e:
                logger.warning(f"Could not load LLM client: {e}. Using default client.")
        
        embedding_model = None
        if not embedding_model and embedding_model_filepath:
            try:
                embedding_model = pickle.load(open(embedding_model_filepath, "rb"))
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}. Using default embedding model.")

        logger.info("Building the KnowledgeBase instance...")
        kb = cls(
            data=data,
            columns=config.get("columns"),
            llm_client=llm_client,
            embedding_model=embedding_model,
            chunk_size=config.get("chunk_size", 2048),
            seed = config.get("seed"),
            min_topic_size=config.get("min_topic_size"),
        )

        # Load embeddings if available
        if embeddings_filepath:
            try:
                kb._store_embeddings_inst(np.load(embeddings_filepath))
            except Exception as e:
                logger.warning(f"Could not load embeddings: {e}.")
        
        if reduced_embeddings_filepath:
            try:
                kb._store_reduced_embeddings_inst(np.load(reduced_embeddings_filepath))
            except Exception as e:
                logger.warning(f"Could not load reduced embeddings: {e}.")

        logger.info("KnowledgeBase loaded successfully.")
        return kb

    @classmethod
    def load_from_hf_hub(
        cls, 
        repo_id: str, 
        hf_token: Optional[str] = None, 
        llm_client: Optional[LLMClient] = None,
        embedding_model: Optional[BaseEmbedding] = None,
        **hf_hub_kwargs) -> "KnowledgeBase":
        """
        Load a KnowledgeBase from the Hugging Face Hub.

        This method retrieves the necessary files from the specified Hugging Face Hub repository
        and reconstructs a KnowledgeBase instance using the stored data, embeddings, and configuration.

        Parameters
        ----------
        repo_id : str
            The repository ID on the Hugging Face Hub (e.g., "org-name/my-knowledge-base").
        hf_token : str, optional
            Hugging Face token for authentication. If None, the local token will be used.
        llm_client : LLMClient, optional
            An optional LLMClient instance. If not provided, it will be loaded from the repository.
        embedding_model : BaseEmbedding, optional
            An optional embedding model instance. If not provided, it will be loaded from the repository.
        **hf_hub_kwargs : dict
            Additional keyword arguments to pass to the Hugging Face Hub download function.

        Returns
        -------
        KnowledgeBase
            An instance of the KnowledgeBase class loaded with the data, configuration, and models from the specified repository.

        Raises
        ------
        ValueError
            If the required "knowledge_base.parquet" file cannot be downloaded.

        Notes
        -----
        - The repository must contain the following files:
          - "knowledge_base.parquet": The raw data for the KnowledgeBase.
        - Optional files:
          - "config.json": A JSON file containing configuration parameters.
          - "embeddings.npy": A NumPy file containing precomputed embeddings.
          - "reduced_embeddings.npy": A NumPy file containing reduced embeddings.
          - "llm_client.pkl": A serialized LLMClient object (if llm_client is not provided).
          - "embedding_model.pkl": A serialized embedding model object (if embedding_model is not provided).
        """

        filepaths = {}
        for filename in cls._saving_filenames:
            key = filename.split('.')[0] + "_filepath"
            try:
                filepaths[key] = hf_hub_download(repo_id, filename=filename, repo_type="dataset", token=hf_token, **hf_hub_kwargs)
            except Exception as e:
                logger.warning(f"Failed to download {filename}: {e}")
                if filename == "knowledge_base.parquet":
                    raise ValueError(f"Failed to download {filename}. Cannot load the KnowledgeBase without it.")
                filepaths[key] = None
        
        return cls._load(**filepaths, llm_client=llm_client, embedding_model=embedding_model)

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

    def _store_embeddings_inst(self, embeddings_inst: np.ndarray):
        self._embeddings_inst = embeddings_inst
        for doc, emb in zip(self._documents, self._embeddings_inst):
            doc.embeddings = emb

    def _store_reduced_embeddings_inst(self, reduced_embeddings_inst: np.ndarray):
        self._reduced_embeddings_inst = reduced_embeddings_inst
        for doc, emb in zip(self._documents, self._reduced_embeddings_inst):
            doc.reduced_embeddings = emb

    @property
    def _config(self):
        if not self._config_inst:
            self._config_inst = {
                "columns": self._columns,
                "chunk_size": self.chunk_size,
                "min_topic_size": self._min_topic_size,
                "language": self._language,
                "seed": self.seed,
                "embedding_model": getattr(self._embedding_model, "model_name", None)
            }
        return self._config_inst

    @property
    def _embeddings(self):
        if self._embeddings_inst is None:
            logger.debug("Computing Knowledge Base embeddings.")
            embeddings_inst = np.array(self._embedding_model.embed([doc.content for doc in self._documents]))
            self._store_embeddings_inst(embeddings_inst)
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
            self._store_reduced_embeddings_inst(reducer.fit_transform(self._embeddings))
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

    def get_random_documents(self, n: int, with_replacement=False):
        if with_replacement:
            return list(self._rng.choice(self._documents, n, replace=True))

        docs = list(self._rng.choice(self._documents, min(n, len(self._documents)), replace=False))

        if len(docs) <= n:
            docs.extend(self._rng.choice(self._documents, n - len(docs), replace=True))

        return docs

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
