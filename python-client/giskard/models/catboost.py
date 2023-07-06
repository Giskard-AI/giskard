import mlflow

from .sklearn import SKLearnModel


class CatboostModel(SKLearnModel):
    """Automatically wraps ``catboost`` models for use with Giskard."""

    _feature_names_attr = "feature_names_"

    def save_model(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.catboost.save_model(self.model, path=local_path, mlflow_model=mlflow_meta)

    @classmethod
    def load_model(cls, local_dir):
        return mlflow.catboost.load_model(local_dir)
