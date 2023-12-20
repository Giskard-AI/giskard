import re
from pathlib import Path

from typing import Union, Optional, Tuple

from giskard.core.core import SupportedModelTypes
from giskard.models.base import BaseModel, WrapperModel
from giskard.models.base.model import MODEL_CLASS_PKL
from giskard.models.sklearn import SKLearnModel
from tests.utils import MockedClient


def test_custom_model(linear_regression_diabetes: BaseModel):
    with MockedClient() as (client, mr):

        class MyModel(WrapperModel):
            @classmethod
            def load_model(cls, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *args, **kwargs):
                pass

            def save_model(self, local_path: Union[str, Path], *args, **kwargs) -> None:
                pass

            def model_predict(self, df):
                pass

            def save(self, local_path: Union[str, Path], *args, **kwargs) -> None:
                super().save(local_path, *args, **kwargs)

            should_save_model_class = True

        def has_model_class_been_sent():
            artifact_url_prefix = "http://giskard-host:12345/api/v2/artifacts/pk/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/"
            return len([i for i in mr.request_history if re.match(artifact_url_prefix + MODEL_CLASS_PKL, i.url)]) > 0

        SKLearnModel(linear_regression_diabetes.model, model_type=SupportedModelTypes.REGRESSION).upload(client, "pk")
        assert not has_model_class_been_sent()

        MyModel(model=linear_regression_diabetes.model, model_type=SupportedModelTypes.REGRESSION).upload(client, "pk")
        assert has_model_class_been_sent()
