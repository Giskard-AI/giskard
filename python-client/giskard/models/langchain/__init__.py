from typing import Iterable, Optional

import mlflow

from giskard.core.core import ModelType, SupportedModelTypes
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import MLFlowBasedModel


class LangchainModel(MLFlowBasedModel):

    @configured_validate_arguments
    def __init__(self,
                 model,
                 model_type: ModelType,
                 name: Optional[str] = None,
                 feature_names: Optional[Iterable] = None,
                 **kwargs) -> None:
        assert model_type == SupportedModelTypes.GENERATIVE, 'LangchainModel only support generative ModelType'

        with mlflow.start_run():
            logged_model = mlflow.langchain.log_model(model, "langchain_model")

        loaded_model = mlflow.pyfunc.load_model(logged_model.model_uri)

        super().__init__(
            model=loaded_model,
            model_type=model_type,
            name=name,
            feature_names=feature_names,
        )

    def save_model(self, local_path, mlflow_meta):
        mlflow.sklearn.save_model(
            self.model, path=local_path, pyfunc_predict_fn='predict', mlflow_model=mlflow_meta
        )

    @classmethod
    def load_model(cls, local_dir):
        return mlflow.sklearn.load_model(local_dir)

    def model_predict(self, df):
        return self.model.predict(df)
