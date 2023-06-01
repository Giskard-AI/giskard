import mlflow

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model


class SKLearnModel(Model):
    def __init__(self, clf, model_type: SupportedModelTypes, name: str = None, data_preprocessing_function=None,
                 feature_names=None, classification_threshold=0.5, classification_labels=None, loader_module:
                 str='giskard.models.sklearn',  loader_class: str = 'SKLearnModel') -> None:

        if classification_labels is None and hasattr(clf, 'classes_'):
            classification_labels = list(getattr(clf, 'classes_'))
        if feature_names is None and hasattr(clf, 'feature_names_in_'):
            feature_names = list(getattr(clf, 'feature_names_in_'))

        super().__init__(clf, model_type, name, data_preprocessing_function, feature_names,
                         classification_threshold, classification_labels, loader_module, loader_class)

    @staticmethod
    def read_model_from_local_dir(local_path):
        return mlflow.sklearn.load_model(local_path)

    def _raw_predict(self, data):
        if self.is_regression:
            return self.clf.predict(data)
        else:
            return self.clf.predict_proba(data)