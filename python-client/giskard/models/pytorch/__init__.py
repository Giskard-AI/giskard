import mlflow

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model


class PyTorchModel(Model):
    def __init__(self, clf, model_type: SupportedModelTypes, name: str = None, data_preparation_function=None,
                 feature_names=None, classification_threshold=0.5, classification_labels=None) -> None:

        super().__init__(clf, model_type, name, data_preparation_function, feature_names,
                         classification_threshold, classification_labels)

    @classmethod
    def read_model_from_local_dir(cls, local_path):
        return mlflow.pytorch.load_model(local_path)


    def save_to_local_dir(self, local_path):

        info = self._new_mlflow_model_meta()
        mlflow.pytorch.save_model(self.clf,
                                  path=local_path,
                                  pyfunc_predict_fn='predict',
                                  mlflow_model=info)
        with open(Path(local_path) / 'giskard-model-meta.yaml', 'w') as f:
            yaml.dump(
                {
                    "language_version": info.flavors['python_function']['python_version'],
                    "language": "PYTHON",
                    "model_type": self.meta.model_type.name.upper(),
                    "threshold": self.meta.classification_threshold,
                    "feature_names": self.meta.feature_names,
                    "classification_labels": self.meta.classification_labels,
                    "id": info.model_uuid,
                    "name": self.meta.name,
                    "size": get_size(local_path),
                }, f, default_flow_style=False)

        return info

    def _raw_predict(self, data):
        # TODO: we should probably move it to load() as a last step and allocate it as an atrribute instead of creating
        # TODO: this object every time we call _raw_predict
        PyTorchWrapper = mlflow.pytorch._PyTorchWrapper(self.clf)
        return PyTorchWrapper.predict(data)