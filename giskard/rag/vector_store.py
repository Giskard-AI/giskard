from typing import Optional, Sequence

import numpy as np
import pandas as pd
from faiss import IndexFlatL2

from .embeddings import EmbeddingsBase


class Document:
    def __init__(self, document: dict, features: Optional[Sequence] = None):
        if len(document) == 1:
            self.page_content = list(document.values())[0]
        elif features is not None and any([feat in document for feat in features]):
            if len(features) == 1:
                self.page_content = document[features[0]]
            else:
                self.page_content = "\n".join([f"{feat}: {document[feat]}" for feat in features])
        else:
            self.page_content = "\n".join([f"{key}: {value}" for key, value in document.items()])

        self.metadata = document


class VectorStore:
    def __init__(self, documents: Sequence[Document], embeddings: np.array, embedding_model: EmbeddingsBase):
        if len(embeddings) == 0 or len(documents) == 0:
            raise ValueError("Documents and embeddings must contains at least one element.")
        if len(embeddings) != len(documents):
            raise ValueError("Documents and embeddings must have the same length.")

        self.embeddings = embeddings
        self.documents = documents
        self.embedding_model = embedding_model

        self.dimension = self.embeddings[0].shape[0]
        self.index = IndexFlatL2(self.dimension)
        self.index.add(self.embeddings)

    @classmethod
    def from_df(cls, df: pd.DataFrame, embedding_model: EmbeddingsBase, features: Sequence[str] = None):
        if len(df) > 0:
            documents = [Document(knowledge_chunk, features=features) for knowledge_chunk in df.to_dict("records")]
            embeddings = embedding_model.embed_documents(documents).astype("float32")
            return cls(documents, embeddings, embedding_model)
        else:
            raise ValueError("Cannot generate a vector store from empty DataFrame.")

    def similarity_search_with_score(self, query, k):
        query_emb = self.embedding_model.embed_text(query).astype("float32")
        distances, indices = self.index.search(query_emb[None, :], k)
        return [(self.documents[i], d) for d, i in zip(distances[0], indices[0])]
