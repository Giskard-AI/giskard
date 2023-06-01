import mlflow
from pathlib import Path
import yaml
import numpy as np

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model
from giskard.path_utils import get_size


class TensorFlowModel(Model):
    def __init__(self, clf, model_type: SupportedModelTypes, name: str = None, data_preparation_function=None,
                 feature_names=None, classification_threshold=0.5, classification_labels=None,
                 loader_module:str = 'giskard.models.tensorflow', loader_class:str = 'TensorFlowModel') -> None:

        super().__init__(clf, model_type, name, data_preparation_function, feature_names,
                         classification_threshold, classification_labels, loader_module, loader_class)

    @classmethod
    def read_model_from_local_dir(cls, local_path):
        return mlflow.tensorflow.load_model(local_path)


    def save_to_local_dir(self, local_path):
        #import pydevd_pycharm
        #pydevd_pycharm.settrace('localhost', port=11223, stdoutToServer=True, stderrToServer=True)

        info = self._new_mlflow_model_meta()

        # mlflow.__version__ == 1.30.0
        save_model_kwargs = dict(
            tf_saved_model_dir=local_path,
            tf_meta_graph_tags=[tag_constants.SERVING],
            tf_signature_def_key="predict",
        )

        mlflow.tensorflow.save_model(self.clf,
                                  path=local_path,
                                  mlflow_model=info)
        with open(Path(local_path) / 'giskard-model-meta.yaml', 'w') as f:
            yaml.dump(
                {
                    "language_version": info.flavors['python_function']['python_version'],
                    "loader_module": self.meta.loader_module,
                    "loader_class": self.meta.loader_class,
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
        if self.is_regression:
            return self.clf.predict(data)
        else:
            predictions = self.clf.predict(data)
            predictions = np.insert(predictions, 1, 1 - predictions[:, 0], axis=1)
            return predictions