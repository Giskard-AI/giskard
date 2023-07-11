from giskard.models.sklearn import SKLearnModel
import mlflow


class CatboostModel(SKLearnModel):
    """
    A subclass of the SKLearnModel class for using the Catboost model.

    The CatboostModel class is a wrapper around the Catboost machine learning library.

    Inherits all attributes and methods from the SKLearnModel class.

    Attributes:
        _feature_names_attr (str): A string attribute indicating the name of the feature names attribute for the Catboost model.

    """

    _feature_names_attr = "feature_names_"

    def save_model(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.catboost.save_model(self.model, path=local_path, mlflow_model=mlflow_meta)

    def to_mlflow(self, artifact_path: str = "catboost-model-from-giskard", **kwargs):
        return mlflow.catboost.log_model(self.model, artifact_path, **kwargs)
