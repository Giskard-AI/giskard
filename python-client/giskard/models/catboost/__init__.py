from typing import Union

import mlflow

from giskard.core.core import SupportedModelTypes
from giskard.core.model import MLFlowBasedModel


class CatboostModel(MLFlowBasedModel):

    def __init__(self, clf, model_type: Union[SupportedModelTypes, str], data_preprocessing_function=None,
                 name: str = None, feature_names=None, classification_threshold=0.5,
                 classification_labels=None) -> None:

        if classification_labels is None and hasattr(clf, 'classes_'):
            classification_labels = list(getattr(clf, 'classes_'))
        if feature_names is None and hasattr(clf, 'feature_names_'):
            feature_names = list(getattr(clf, 'feature_names_'))

        super().__init__(clf=clf,
                         model_type=model_type,
                         data_preprocessing_function=data_preprocessing_function,
                         name=name,
                         feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)

    def save_with_mflow(self, local_path, mlflow_meta: mlflow.models.Model):
        if self.is_classification:
            pyfunc_predict_fn = 'predict_proba'
        elif self.is_regression:
            pyfunc_predict_fn = 'predict'
        else:
            raise ValueError('Unsupported model type')

        mlflow.catboost.save_model(self.clf,
                                   path=local_path,
                                   pyfunc_predict_fn=pyfunc_predict_fn,
                                   mlflow_model=mlflow_meta)

    @classmethod
    def load_clf(cls, local_dir):
        return mlflow.catboost.load_model(local_dir)

    def clf_predict(self, df):
        return self.clf.predict_proba(df)
