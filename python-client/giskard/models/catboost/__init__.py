from typing import Union
from giskard.core.core import SupportedModelTypes
from giskard.models.base import MLFlowBasedModel

try:
    import mlflow
except ImportError:
    pass


class CatboostModel(MLFlowBasedModel):
    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 name: str = None,
                 data_preprocessing_function=None,
                 model_postprocessing_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:

        if classification_labels is None and hasattr(clf, "classes_"):
            classification_labels = list(getattr(clf, "classes_"))
        if feature_names is None and hasattr(clf, "feature_names_"):
            if data_preprocessing_function is None:
                feature_names = list(getattr(clf, "feature_names_"))
            else:
                raise ValueError("feature_names must be provided if data_preprocessing_function is not None.")

        super().__init__(
            clf=clf,
            model_type=model_type,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            name=name,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
        )

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.catboost.save_model(
            self.clf, path=local_path, mlflow_model=mlflow_meta
        )

    @classmethod
    def load_clf(cls, local_dir):
        return mlflow.catboost.load_model(local_dir)

    def clf_predict(self, df):
        if self.is_classification:
            return self.clf.predict_proba(df)
        elif self.is_regression:
            return self.clf.predict(df)
        else:
            raise ValueError("Unsupported model type")
