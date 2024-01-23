import pytest

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
    model = FailingModel(model_type="regression")
    regex_model_name = str(model).replace("(", "\\(").replace(")", "\\)")

    with MockedClient() as (client, mr), pytest.warns(
        UserWarning,
        match=f"Failed to upload {regex_model_name} used in the test suite. The test suite will be partially uploaded.",
    ):
        utils.register_uri_for_artifact_meta_info(mr, my_test, None)

        test_suite = Suite().add_test(my_test, model=model)

        test_suite.upload(client, "titanic")
