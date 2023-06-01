from giskard.models.sklearn import SKLearnModel

try:
    import mlflow
except ImportError as e:
    raise ImportError("Please install it via 'pip install mlflow-skinny'") from e


class CatboostModel(SKLearnModel):

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.catboost.save_model(
            self.clf, path=local_path, mlflow_model=mlflow_meta
        )
