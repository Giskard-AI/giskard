import json
from io import BytesIO

import httpretty
import numpy as np
import pandas as pd
import pytest
from requests_toolbelt.multipart import decoder

from giskard.client.giskard_client import GiskardClient
from giskard.client.io_utils import decompress, load_decompress
from giskard.client.model import GiskardModel
from giskard.client.project import GiskardProject
from giskard.ml_worker.core.giskard_dataset import GiskardDataset

url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "multipart/form-data; boundary="
model_name = "uploaded model"
b_content_type = b"application/json"


@httpretty.activate(verbose=True, allow_net_connect=False)
def test_upload_df(diabetes_dataset: GiskardDataset):
    httpretty.register_uri(httpretty.POST, "http://giskard-host:12345/api/v2/project/data/upload")
    dataset_name = "diabetes dataset"
    client = GiskardClient(url, token)
    project = GiskardProject(client.session, "test-project", 1)

    with pytest.raises(Exception):  # Error Scenario
        project.upload_df(
            df=diabetes_dataset.df,
            column_types=diabetes_dataset.feature_types,
            target=diabetes_dataset.target,
            name=dataset_name,
        )
    with pytest.raises(Exception):  # Error Scenario
        project.upload_df(df=diabetes_dataset.df, column_types={"test": "test"}, name=dataset_name)

    project.upload_df(
        df=diabetes_dataset.df, column_types=diabetes_dataset.feature_types, name=dataset_name
    )

    req = httpretty.last_request()
    assert req.headers.get("Authorization") == auth
    assert int(req.headers.get("Content-Length")) > 0
    assert req.headers.get("Content-Type").startswith(content_type)

    multipart_data = decoder.MultipartDecoder(req.body, req.headers.get("Content-Type"))
    assert len(multipart_data.parts) == 2
    meta, upload_file = multipart_data.parts
    assert meta.headers.get(b"Content-Type") == b_content_type
    pd.testing.assert_frame_equal(
        diabetes_dataset.df, pd.read_csv(BytesIO(decompress(upload_file.content)))
    )


@httpretty.activate(verbose=True, allow_net_connect=False)
def _test_upload_model(model: GiskardModel, ds: GiskardDataset):
    httpretty.register_uri(httpretty.POST, "http://giskard-host:12345/api/v2/project/models/upload")

    client = GiskardClient(url, token)
    project = GiskardProject(client.session, "test-project", 1)
    if model.model_type == "regression":
        # Warning Scenario: classification_labels is sent for regression model
        with pytest.warns(UserWarning):
            project.upload_model(
                prediction_function=model.prediction_function,
                model_type=model.model_type,
                feature_names=model.feature_names,
                name=model_name,
                validate_df=ds.df,
                classification_labels=model.classification_labels
            )
    else:
        project.upload_model(
            prediction_function=model.prediction_function,
            model_type=model.model_type,
            feature_names=model.feature_names,
            name=model_name,
            validate_df=ds.df,
            classification_labels=model.classification_labels,
        )

    req = httpretty.last_request()
    assert req.headers.get("Authorization") == auth
    assert int(req.headers.get("Content-Length")) > 0
    assert req.headers.get("Content-Type").startswith(content_type)

    multipart_data = decoder.MultipartDecoder(req.body, req.headers.get("Content-Type"))
    assert len(multipart_data.parts) == 3
    meta, model_file, requirements_file = multipart_data.parts

    if model.model_type == "classification":
        metadata = json.loads(meta.content)
        assert np.array_equal(model.classification_labels, metadata.get("classificationLabels"))

    assert meta.headers.get(b'Content-Type') == b_content_type
    loaded_model = load_decompress(model_file.content)

    assert np.array_equal(loaded_model(ds.df), model.prediction_function(ds.df))
    assert requirements_file.content.decode()


def _test_upload_model_exceptions(model: GiskardModel, ds: GiskardDataset):
    client = GiskardClient(url, token)
    project = GiskardProject(client.session, "test-project", 1)

    # Error Scenario : Column_types dictionary sent as feature_names
    with pytest.raises(Exception):
        project.upload_model(
            prediction_function=model.prediction_function,
            model_type=model.model_type,
            feature_names=model.feature_names,
            name=model_name,
            validate_df=ds.df,
            classification_labels=model.classification_labels
        )

    if model.model_type == 'classification':
        # Error Scenario: Classification model sent without classification_labels
        with pytest.raises(Exception):
            project.upload_model_and_df(
                prediction_function=model.prediction_function,
                model_type=model.model_type,
                df=ds.df,
                column_types=ds.feature_types,
                feature_names=model.feature_names,
                model_name=model_name,
                target='default'
            )

        # Error Scenario: Target has values not declared in Classification Label
        with pytest.raises(Exception):
            project.upload_model_and_df(
                prediction_function=model.prediction_function,
                model_type=model.model_type,
                target='default',
                df=ds.df,
                column_types=ds.feature_types,
                feature_names=model.feature_names,
                model_name=model_name,
                classification_labels=[0, 1]
            )


@pytest.mark.parametrize(
    "data,model,",
    [
        ("german_credit_data", "german_credit_model"),
        ("diabetes_dataset", "linear_regression_diabetes"),
    ],
)
def test_upload_models(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    _test_upload_model(model, data)


@pytest.mark.parametrize('data,model,',
                         [('german_credit_data', 'german_credit_model'),
                          ('diabetes_dataset', 'linear_regression_diabetes')])
def test_upload_models_exceptions(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    _test_upload_model_exceptions(model, data)
