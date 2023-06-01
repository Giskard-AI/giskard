import shutil
from pathlib import Path
from typing import Union

import cloudpickle

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model


def test_custom_model():
    class MyModel(Model):
        def __init__(self, clf, model_type: Union[SupportedModelTypes, str], name: str = None,
                     data_preprocessing_function=None, feature_names=None, classification_threshold=0.5,
                     classification_labels=None) -> None:
            super().__init__(clf, model_type, name, data_preprocessing_function, feature_names,
                             classification_threshold, classification_labels)

        def save_to_local_dir(self, local_path):
            with open(Path(local_path) / "foo_model", 'w') as f:
                f.write("model content")
            with open(Path(local_path) / "ModelClass", 'wb') as f:
                import cloudpickle
                content = cloudpickle.dumps(self.__class__)
                f.write(content)

            return self._new_mlflow_model_meta()

        @staticmethod
        def read_model_from_local_dir(local_path: str):
            cloudpickle.loads(open(Path(local_path) / "ModelClass", 'rb').read())
            return {}

    model_id = MyModel({}, model_type=SupportedModelTypes.REGRESSION, name="test custom model").save(None, "pk")
    mpath = Path(f'/Users/andreyavtomonov/giskard-home/cache/pk/models/{model_id}')
    mpath.mkdir(parents=True)
    shutil.copyfile(
        '/Users/andreyavtomonov/projects/work/giskard/backend/src/main/resources/demo_projects/credit/models/93112387-7bce-4b71-826e-933cfb235a65/giskard-model-meta.yaml',
        f'{mpath / "giskard-model-meta.yaml"}')

    model = Model.load(None, "pk", model_id)
    model
