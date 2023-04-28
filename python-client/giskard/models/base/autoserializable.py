from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Iterable, Union

import cloudpickle
import pickle
import numpy as np
import pandas as pd
import mlflow
import yaml

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

    def _postprocess(self, raw_predictions):

        # Convert predictions to numpy array
        raw_predictions = self._convert_to_numpy(raw_predictions)

        # We try to automatically fix issues in the output shape
        raw_predictions = self._possibly_fix_predictions_shape(raw_predictions)

        return raw_predictions

    @configured_validate_arguments
    def predict_df(self, df: pd.DataFrame):
        raw_prediction = self.model_predict(df)
        raw_prediction = self._postprocess(raw_prediction)

        return raw_prediction

    def _convert_to_numpy(self, raw_predictions):
        return np.asarray(raw_predictions)

    def _possibly_fix_predictions_shape(self, raw_predictions):
        if not self.is_classification:
            return raw_predictions

        # Ensure this is 2-dimensional
        if raw_predictions.ndim <= 1:
            raw_predictions = raw_predictions.reshape(-1, 1)

        # Fix possible extra dimensions (e.g. batch dimension which was not squeezed)
        if raw_predictions.ndim > 2:
            logger.warning(
                f"\nThe output of your model has shape {raw_predictions.shape}, but we expect a shape (n_entries, n_classes). \n"
                "We will attempt to automatically reshape the output to match this format, please check that the results are consistent.",
                exc_info=True,
            )

            raw_predictions = raw_predictions.squeeze(tuple(range(1, raw_predictions.ndim - 1)))

            if raw_predictions.ndim > 2:
                raise ValueError(
                    f"The output of your model has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes)."
                )

        # E.g. for binary classification, prediction should be of the form `(p, 1 - p)`.
        # If a binary classifier returns a single prediction `p`, we try to infer the second class
        # prediction as `1 - p`.
        if self.is_binary_classification and raw_predictions.shape[-1] == 1:
            logger.warning(
                f"\nYour binary classification model prediction is of the shape {raw_predictions.shape}. \n"
                f"In Giskard we expect the shape {(raw_predictions.shape[0], 2)} for binary classification models. \n"
                "We automatically inferred the second class prediction but please make sure that \n"
                "the probability output of your model corresponds to the first label of the \n"
                f"classification_labels ({self.meta.classification_labels}) you provided us with.",
                exc_info=True,
            )

            raw_predictions = np.append(raw_predictions, 1 - raw_predictions, axis=1)

        # For classification models, the last dimension must be equal to the number of classes
        if raw_predictions.shape[-1] != len(self.meta.classification_labels):
            raise ValueError(
                f"The output of your model has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes), \n"
                f"where `n_classes` is the number of classes in your model output ({len(self.meta.classification_labels)} in this case)."
            )

        return raw_predictions

    @abstractmethod
    def model_predict(self, df):
        ...

    def save(self, local_path: Union[str, Path]) -> None:
        giskard_class = infer_ml_library(self.model)
        self.meta.loader_class = giskard_class.__name__
        self.meta.loader_module = giskard_class.__module__
        super().save(local_path)
        self.save_model(local_path)

    def save_model(self, local_path: Union[str, Path]) -> None:
        giskard_class = infer_ml_library(self.model)
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

    @classmethod
    def load_data_preprocessing_function(cls, local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-data-preprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return cloudpickle.load(f)
        else:
            return None

    @classmethod
    def load_model_postprocessing_function(cls, local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-model-postprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return cloudpickle.load(f)
        else:
            return None
