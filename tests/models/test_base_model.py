import numpy as np
import pandas as pd
import pytest

from giskard.models.base.model import BaseModel

from tests import utils


class _CustomModel(BaseModel):
    def predict_df(self, df: pd.DataFrame):
        return np.ones(len(df))


def test_base_model_raises_error_for_unknown_model_type():
    assert _CustomModel("regression")  # this is ok

    with pytest.raises(ValueError):
        _CustomModel("invalid")


def test_base_model_raises_error_if_duplicated_target_labels():
    assert _CustomModel("classification", classification_labels=["one", "two"])

    with pytest.raises(ValueError):
        _CustomModel("classification", classification_labels=["one", "two", "one"])


def test_base_model_raises_error_if_classification_labels_not_provided():
    assert _CustomModel("classification", classification_labels=["one", "two"])

    with pytest.raises(ValueError):
        _CustomModel("classification")


# Tests for model download
def test_model_download(request):
    model: BaseModel = request.getfixturevalue("german_credit_model")
    project_key = "test-project"

    with utils.MockedClient(mock_all=False) as (client, mr):
        # The model needs to request files
        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)

        downloaded_model = BaseModel.download(client=client, project_key=project_key, model_id=str(model.id))

        assert downloaded_model.id == model.id
        assert downloaded_model.meta == model.meta


def test_model_download_with_cache(request):
    model: BaseModel = request.getfixturevalue("german_credit_model")
    project_key = "test-project"

    utils.local_save_model_under_giskard_home_cache(model=model, project_key=project_key)

    with utils.MockedClient(mock_all=False) as (client, mr):
        # The model is cached, can be created without further requests
        utils.register_uri_for_model_meta_info(mr, model, project_key)

        downloaded_model = BaseModel.download(client=client, project_key=project_key, model_id=str(model.id))

        assert downloaded_model.id == model.id
        assert downloaded_model.meta == model.meta
