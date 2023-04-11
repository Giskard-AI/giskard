from typing import Callable, Iterable, Any, Optional

import pandas as pd

import mlflow
from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import MLFlowBasedModel


class SKLearnModel(MLFlowBasedModel):
    @configured_validate_arguments
    def __init__(self,
                 clf,
                 model_type: ModelType,
                 name: Optional[str] = None,
                 data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                 model_postprocessing_function: Callable[[Any], Any] = None,
                 feature_names: Optional[Iterable] = None,
                 classification_threshold: float = 0.5,
                 classification_labels: Optional[Iterable] = None) -> None:

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
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
        )

    def save_with_mlflow(self, local_path, mlflow_meta):
        if self.is_classification:
            pyfunc_predict_fn = "predict_proba"
        elif self.is_regression:
            pyfunc_predict_fn = "predict"
        else:
            raise ValueError("Unsupported model type")

        mlflow.sklearn.save_model(
            self.clf, path=local_path, pyfunc_predict_fn=pyfunc_predict_fn, mlflow_model=mlflow_meta
        )

    @classmethod
    def load_clf(cls, local_dir):
        return mlflow.sklearn.load_model(local_dir)

    def clf_predict(self, df):
        if self.is_regression:
            return self.clf.predict(df)
        else:
            return self.clf.predict_proba(df)
