import numpy as np
import pandas as pd
import pytest
import uuid

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
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        with utils.MockedClient(mock_all=False) as (client, mr):
            # The model needs to request files
            requested_urls = []
            requested_urls.extend(utils.register_uri_for_model_meta_info(mr, model, project_key))
            requested_urls.extend(
                utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)
            )

            downloaded_model = BaseModel.download(client=client, project_key=project_key, model_id=str(model.id))

            for requested_url in requested_urls:
                assert utils.is_url_requested(mr.request_history, requested_url)

            assert downloaded_model.id == model.id
            assert downloaded_model.meta == model.meta


def test_model_download_with_cache(request):
    model: BaseModel = request.getfixturevalue("german_credit_model")
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        # Save the model to cache dir
        utils.local_save_model_under_giskard_home_cache(model=model, project_key=project_key)

        with utils.MockedClient(mock_all=False) as (client, mr):
            # The model is cached, can be created without further requests
            requested_urls = utils.register_uri_for_model_meta_info(mr, model, project_key)

            downloaded_model = BaseModel.download(client=client, project_key=project_key, model_id=str(model.id))

            for requested_url in requested_urls:
                assert utils.is_url_requested(mr.request_history, requested_url)

            assert downloaded_model.id == model.id
            assert downloaded_model.meta == model.meta
