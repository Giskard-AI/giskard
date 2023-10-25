import logging
from typing import Any, Callable, Iterable, Optional

import mlflow
import pandas as pd

from .base import MLFlowSerializableModel
from ..core.core import ModelType
from ..core.validation import configured_validate_arguments

logger = logging.getLogger(__name__)


class TensorFlowModel(MLFlowSerializableModel):
    @configured_validate_arguments
    def __init__(
        self,
        model,
        model_type: ModelType,
        name: Optional[str] = None,
        data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
        model_postprocessing_function: Callable[[Any], Any] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            id=id,
            **kwargs,
        )

    @classmethod
    def load_model(cls, local_path):
        return mlflow.tensorflow.load_model(local_path)

    def save_model(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.tensorflow.save_model(self.model, path=local_path, mlflow_model=mlflow_meta)

    def model_predict(self, data):
        return self.model.predict(data)

    def to_mlflow(self, artifact_path: str = "tensorflow-model-from-giskard", **kwargs):
        return mlflow.tensorflow.log_model(self.model, artifact_path, **kwargs)
