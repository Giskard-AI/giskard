import logging
from typing import Optional, Iterable, Any, Callable

import mlflow
import pandas as pd

from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import MLFlowBasedModel

logger = logging.getLogger(__name__)


class TensorFlowModel(MLFlowBasedModel):
    @configured_validate_arguments
    def __init__(self,
                 clf,
                 model_type: ModelType,
                 name: Optional[str] = None,
                 data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                 model_postprocessing_function: Callable[[Any], Any] = None,
                 feature_names: Optional[Iterable] = None,
                 classification_threshold: float = 0.5,
                 classification_labels: Optional[Iterable] = None):
        super().__init__(clf=clf,
                         model_type=model_type,
                         name=name,
                         data_preprocessing_function=data_preprocessing_function,
                         model_postprocessing_function=model_postprocessing_function,
                         feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)

    @classmethod
    def load_clf(cls, local_path):
        return mlflow.tensorflow.load_model(local_path)

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.tensorflow.save_model(self.clf,
                                     path=local_path,
                                     mlflow_model=mlflow_meta)

    def clf_predict(self, data):
        return self.clf.predict(data)
