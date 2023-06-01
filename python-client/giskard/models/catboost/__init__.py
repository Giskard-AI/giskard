from giskard.models.sklearn import SKLearnModel
import mlflow


class CatboostModel(SKLearnModel):

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.catboost.save_model(
            self.clf, path=local_path, mlflow_model=mlflow_meta
        )
