import re

import httpretty

from giskard import Model, SKLearnModel
from giskard.client.giskard_client import GiskardClient
from giskard.core.core import SupportedModelTypes
from giskard.core.model import CustomModel, MODEL_CLASS_PKL

url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "application/json"
model_name = "uploaded model"
b_content_type = b"application/json"


@httpretty.activate(verbose=True, allow_net_connect=False)
def test_custom_model(linear_regression_diabetes: Model):
    artifact_url_prefix = "http://giskard-host:12345/api/v2/artifacts/pk/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/"
    artifact_url_pattern = re.compile(artifact_url_prefix + ".*")
    httpretty.register_uri(httpretty.POST, artifact_url_pattern)
    httpretty.register_uri(httpretty.POST, 'http://giskard-host:12345/api/v2/project/pk/models')

    client = GiskardClient(url, token)

    class MyModel(CustomModel):
        pass

    def has_model_class_been_sent():
        return len([i for i in httpretty.latest_requests() if
                    re.match(artifact_url_prefix + MODEL_CLASS_PKL, i.url)]) > 0

    SKLearnModel(linear_regression_diabetes.clf, model_type=SupportedModelTypes.REGRESSION).save(client, "pk")
    assert not has_model_class_been_sent()

    MyModel(linear_regression_diabetes.clf, model_type=SupportedModelTypes.REGRESSION).save(client, "pk")
    assert has_model_class_been_sent()
