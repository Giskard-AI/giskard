import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import cloudpickle
from langchain.indexes.vectorstore import VectorStoreIndexWrapper, VectorstoreIndexCreator
from langchain.vectorstores import Chroma

from giskard import WrapperModel


class VectorStoreModel(WrapperModel, ABC):
    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 name: str = None,
                 data_preprocessing_function=None,
                 model_postprocessing_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:

        if classification_labels is None and hasattr(clf, "classes_"):
            classification_labels = list(getattr(clf, "classes_"))
        if feature_names is None and hasattr(clf, "feature_names_"):
            feature_names = list(getattr(clf, "feature_names_"))

        super().__init__(
            clf=clf,
            model_type=model_type,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            name=name,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
        )

    def save(self, local_path: Union[str, Path]) -> None:
        """
        MLFlow requires a target directory to be empty before the model is saved, thus we have to call
        save_with_mflow first and then save the rest of the metadata
        """
        if not self.id:
            self.id = uuid.uuid4()

        with open(Path(local_path) / "vectorstore.pkl", "wb") as f:
            cloudpickle.dump(self.clf.vectorstore, f)

        super().save(local_path)

    @classmethod
    def load(cls, local_dir, **kwargs):
        vectorstore = cls.load_clf(local_dir)
        VectorStores
        clf = VectorstoreIndexCreator.from_loaders()
        return cls(clf=vectorstore, **kwargs)

    @classmethod
    @abstractmethod
    def load_clf(cls, local_dir):
        with open(Path(local_dir) / "vectorstore.pkl", "rb") as f:
            cloudpickle.load(f)
