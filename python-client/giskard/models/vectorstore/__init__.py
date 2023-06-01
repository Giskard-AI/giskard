import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import cloudpickle
from langchain import OpenAI
from langchain.chains import RetrievalQA

from giskard.core.model import Model
from langchain.vectorstores import Chroma


class RetrievalQAModel(Model):
    model: RetrievalQA
    should_save_model_class = True
    model_postprocessing_function = None

    def __init__(self,
                 model: RetrievalQA,
                 name: str = None) -> None:
        self.model = model
        super().__init__(
            model_type='regression',
            name=name,
            feature_names=None,
            classification_threshold=None,
            classification_labels=None
        )

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)

        vectorstore: Chroma = self.model.retriever.vectorstore

        try:
            import chromadb
            import chromadb.config
        except ImportError:
            raise ValueError(
                "Could not import chromadb python package. "
                "Please install it with `pip install chromadb`."
            )

        clone = Chroma(persist_directory=(Path(local_path) / 'db').absolute().as_posix(),
                       embedding_function=vectorstore._embedding_function)
        clone._collection.add(**vectorstore._collection.get())

        clone.persist()

        with open(Path(local_path) / "embedding_function.pkl", "wb") as f:
            cloudpickle.dump(vectorstore._embedding_function, f)

    def predict_df(self, df):
        return self.model.apply(list(df))

    @classmethod
    def load(cls, local_dir, **constructor_params):
        with open(Path(local_dir) / "embedding_function.pkl", "rb") as f:
            print('file')
            embedding_function = cloudpickle.load(f)
            print(embedding_function)

            persist_directory = (Path(local_dir) / 'db').absolute().as_posix()
            chroma = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)
            print(chroma)
            chroma.as_retriever()

            return cls(RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=chroma.as_retriever()))

# For inspect= clf predict
# Should save class to true
# Example in the unit tests
