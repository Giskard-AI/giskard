from abc import ABC
from pathlib import Path
from typing import Any, Optional, Iterable, Union
import importlib

import cloudpickle
import pickle
import mlflow
import yaml
import pandas as pd

from giskard.core.core import ModelType, SupportedModelTypes, ModelMeta
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import BaseModel
from giskard.models import infer_ml_library
import logging

logger = logging.getLogger(__name__)


class AutoSerializableModel(BaseModel, ABC):
    """
    A subclass of a BaseModel that wraps an existing model object (model) and uses it to make inference
    """
    should_save_model_class = True
    model: Any

    @configured_validate_arguments
    def __init__(
            self,
            model: Any,
            model_type: ModelType,
            name: Optional[str] = None,
            feature_names: Optional[Iterable] = None,
            classification_threshold: Optional[float] = 0.5,
            classification_labels: Optional[Iterable] = None,
    ) -> None:
        """
        Initialize a new instance of the WrapperModel class.

        Args:
            model (Any): The model that will be wrapped.
            model_type (ModelType): The type of the model. Must be a value from the `ModelType` enumeration.
            name (str, optional): A name for the wrapper. Defaults to None.
            feature_names (Optional[Iterable], optional): A list of feature names. Defaults to None.
            classification_threshold (float, optional): The probability threshold for classification. Defaults to 0.5.
            classification_labels (Optional[Iterable], optional): A list of classification labels. Defaults to None.
        """
        super().__init__(model_type, name, feature_names, classification_threshold, classification_labels)
        self.model = model
        giskard_class = infer_ml_library(self.model)
        self.meta.loader_class = giskard_class.__name__
        self.meta.loader_module = giskard_class.__module__

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)
        self.save_model(local_path)

    def save_model(self, local_path: Union[str, Path]) -> None:
        giskard_class = getattr(importlib.import_module(self.meta.loader_module), self.meta.loader_class)
        if str(giskard_class) in ["SKLearnModel", "CatBoostModel", "PyTorchModel", "TensorFlowModel"]:
            giskard_class.save_model(local_path, mlflow.models.Model(model_uuid=str(self.id)))
        elif str(giskard_class) == "HuggingFaceModel":
            giskard_class.save_model(local_path)
        else:
            try:
                model_file = Path(local_path) / "model.pkl"
                with open(model_file, "wb") as f:
                    cloudpickle.dump(self.model, f, protocol=pickle.DEFAULT_PROTOCOL)
            except ValueError:
                raise ValueError(
                    "We couldn't find a suitable method to serialise your model. Please provide us with your own "
                    "serialisation method by overriding the save_model() and load_model() methods.")

    @classmethod
    def load(cls, local_dir, **kwargs):
        model_file = Path(local_dir)
        assert model_file.exists(), f"Cannot find model {local_dir}."
        with open(model_file / "giskard-model-meta.yaml") as f:
            file_meta = yaml.load(f, Loader=yaml.Loader)
            meta = ModelMeta(
                name=file_meta["name"],
                model_type=SupportedModelTypes[file_meta["model_type"]],
                feature_names=file_meta["feature_names"],
                classification_labels=file_meta["classification_labels"],
                classification_threshold=file_meta["threshold"],
                loader_module=file_meta["loader_module"],
                loader_class=file_meta["loader_class"],
            )
        clazz = cls.determine_model_class(meta, local_dir)
        return cls(model=clazz.load_model(model_file / "model.pkl"), **kwargs)

    @classmethod
    def load_model(cls, local_dir):
        model_path = Path(local_dir)
        if model_path.exists():
            with open(model_path, "rb") as f:
                model = cloudpickle.load(f)
                return model
        else:
            raise ValueError(
                f"Cannot load model with cloudpickle, "
                f"{model_path} file not found and 'load_model' method isn't overriden"
            )

    def predict_proba(self, df: pd.DataFrame):
        giskard_class = getattr(importlib.import_module(self.meta.loader_module), self.meta.loader_class)
        return giskard_class.predict_proba(df)
