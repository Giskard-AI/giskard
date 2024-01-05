from typing import Optional, Tuple

import mlflow

from .sklearn import SKLearnModel


class CatboostModel(SKLearnModel):
    """Automatically wraps ``catboost`` models for use with Giskard."""

    _feature_names_attr = "feature_names_"

    def save_model(self, local_path, mlflow_meta: mlflow.models.Model, *args, **kwargs):
        mlflow.catboost.save_model(self.model, path=local_path, mlflow_model=mlflow_meta)

    @classmethod
    def load_model(cls, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *args, **kwargs):
        return mlflow.catboost.load_model(local_dir)

    def to_mlflow(self, artifact_path: str = "catboost-model-from-giskard", **kwargs):
        return mlflow.catboost.log_model(self.model, artifact_path, **kwargs)
