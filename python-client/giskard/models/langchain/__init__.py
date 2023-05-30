from typing import Iterable, Optional, Callable, Any

import mlflow
import pandas as pd

from giskard.core.core import ModelType, SupportedModelTypes
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import MLFlowBasedModel


class LangchainModel(MLFlowBasedModel):

    @configured_validate_arguments
    def __init__(self,
                 model,
                 model_type: ModelType,
                 name: Optional[str] = None,
                 data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                 model_postprocessing_function: Callable[[Any], Any] = None,
                 feature_names: Optional[Iterable] = None,
                 classification_threshold: Optional[float] = 0.5,
                 classification_labels: Optional[Iterable] = None) -> None:
        assert model_type == SupportedModelTypes.GENERATIVE, 'LangchainModel only support generative ModelType'

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

    def save_model(self, local_path, mlflow_meta):
        mlflow.langchain.save_model(
            self.model, path=local_path, mlflow_model=mlflow_meta
        )

    @classmethod
    def load_model(cls, local_dir):
        return mlflow.langchain.load_model(local_dir)

    def model_predict(self, df):
        return [self.model.predict(**data) for data in df.to_dict('index').values()]
