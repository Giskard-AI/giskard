import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import cloudpickle
from langchain import OpenAI
from langchain.chains import RetrievalQA

from giskard.core.model import CustomModel
from langchain.vectorstores import Chroma
import pandas as pd


class RetrievalQAModel(CustomModel):
    model: RetrievalQA

    def __init__(self,
                 model: RetrievalQA,
                 name: str = None) -> None:
        self.model = model
        super().__init__(
            model_type='LLM',
            name=name,
            feature_names=None,
            classification_threshold=None,
            classification_labels=None
        )

    def save(self, local_path: Union[str, Path]) -> None:
        """
        MLFlow requires a target directory to be empty before the model is saved, thus we have to call
        save_with_mflow first and then save the rest of the metadata
        """
        if not self.id:
            self.id = uuid.uuid4()

        vectorstore: Chroma = self.model.retriever.vectorstore

        # Save previous state to not alter user settings
        tmp_persist_directory = vectorstore._persist_directory
        tmp_client_settings = vectorstore._client_settings
        tmp_client = vectorstore._client

        try:
            import chromadb
            import chromadb.config
        except ImportError:
            raise ValueError(
                "Could not import chromadb python package. "
                "Please install it with `pip install chromadb`."
            )

        vectorstore._persist_directory = (Path(local_path) / str(self.id) / "db").absolute().as_posix()
        vectorstore._client_settings = chromadb.config.Settings(
            chroma_db_impl="duckdb+parquet", persist_directory=vectorstore._persist_directory
        )
        vectorstore._client = chromadb.Client(vectorstore._client_settings)
        vectorstore.persist()

        with open(Path(local_path) / str(self.id) / "embedding_function.pkl", "wb") as f:
            cloudpickle.dump(vectorstore._embedding_function, f)

        # Reset data
        vectorstore._persist_directory = tmp_persist_directory
        vectorstore._client_settings = tmp_client_settings
        vectorstore._client = tmp_client

        super().save(local_path)

    def predict_df(self, df: pd.DataFrame):
        return self.model.apply(list(df))

    @classmethod
    def load(cls, local_dir, **constructor_params):
        with open(Path(local_dir) / "embedding_function.pkl", "rb") as f:
            embedding_function = cloudpickle.load(f)

            persist_directory = (Path(local_dir) / "db").absolute().as_posix()
            chroma = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)

            cls(RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=chroma.as_retriever()))

# For inspect= clf predict
# Should save class to true
# Example in the unit tests
