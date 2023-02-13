import mlflow

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model


class CatboostModel(Model):
    def __init__(self, clf, model_type: SupportedModelTypes, name: str = None, data_preprocessing_function=None,
                 feature_names=None, classification_threshold=0.5, classification_labels=None) -> None:

        if classification_labels is None and hasattr(clf, 'classes_'):
            classification_labels = list(getattr(clf, 'classes_'))
        if feature_names is None and hasattr(clf, 'feature_names_'):
            feature_names = list(getattr(clf, 'feature_names_'))

        super().__init__(clf=clf,
                         model_type=model_type,
                         name=name,
                         data_preprocessing_function=data_preprocessing_function,
                         feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)

    @staticmethod
    def read_model_from_local_dir(local_path):
        return mlflow.catboost.load_model(local_path)

    def _save_model_to_local_dir(self, local_path, **kwargs):
        return mlflow.catboost.save_model(self.clf, path=local_path, **kwargs)

    def _raw_predict(self, data):
        return self.clf.predict_proba(data)
