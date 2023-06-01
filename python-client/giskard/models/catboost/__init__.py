from giskard.models.sklearn import SKLearnModel
import mlflow
from typing import Callable, Iterable, Any, Optional

import pandas as pd

from giskard.core.core import ModelType, SupportedModelTypes
from giskard.core.validation import configured_validate_arguments


class CatboostModel(SKLearnModel):

    @configured_validate_arguments
    def __init__(self,
                 model,
                 model_type: ModelType,
                 name: Optional[str] = None,
                 data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                 model_postprocessing_function: Callable[[Any], Any] = None,
                 feature_names: Optional[Iterable] = None,
                 classification_threshold: float = 0.5,
                 classification_labels: Optional[Iterable] = None) -> None:

        if model_type == SupportedModelTypes.CLASSIFICATION:
            if classification_labels is None and hasattr(model, "classes_"):
                classification_labels = list(getattr(model, "classes_"))
        if feature_names is None and hasattr(model, "feature_names_"):
            if data_preprocessing_function is None:
                feature_names = list(getattr(model, "feature_names_"))
            else:
                raise ValueError("feature_names must be provided if data_preprocessing_function is not None.")

        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
        )

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.catboost.save_model(
            self.model, path=local_path, mlflow_model=mlflow_meta
        )
