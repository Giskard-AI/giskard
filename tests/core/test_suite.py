import pytest
import requests_mock

from giskard import Suite, test
from giskard.models.base import BaseModel
from tests import utils
from tests.utils import MockedClient


class FailingModel(BaseModel):
    def upload(self, *args, **kwargs):
        raise ValueError("For testing")

    def predict_df(self, *args, **kwargs):
        return 0


@test
def my_test(model: BaseModel):
    return True


def test_save_suite_with_artifact_error():
    project_key = "project_key"
    model = FailingModel(model_type="regression")
    regex_model_name = str(model).replace("(", "\\(").replace(")", "\\)")

    with MockedClient() as (client, mr), pytest.warns(
        UserWarning,
        match=f"Failed to upload {regex_model_name} used in the test suite. The test suite will be partially uploaded.",
    ):
        utils.register_uri_for_artifact_meta_info(mr, my_test, project_key)
        mr.register_uri(
            method=requests_mock.POST,
            url="http://giskard-host:12345/api/v2/testing/project/project_key/suites",
            json={"id": 1, "tests": [{"id": 2}]},
        )

        test_suite = Suite().add_test(my_test, model=model)

        test_suite.upload(client, project_key)
