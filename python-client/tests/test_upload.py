import re

import httpretty
import pytest

from giskard import Dataset
from giskard import Model
from giskard.client.giskard_client import GiskardClient

url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "application/json"
model_name = "uploaded model"
b_content_type = b"application/json"


@httpretty.activate(verbose=True, allow_net_connect=False)
def test_upload_df(diabetes_dataset: Dataset, diabetes_dataset_with_target: Dataset):
    artifact_url_pattern = re.compile(
        r"http://giskard-host:12345/api/v2/artifacts/test-project/datasets/[a-z0-9]{32}/[data.csv.zst|giskard\-dataset\-meta.yaml]")
    datasets_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/datasets")

    httpretty.register_uri(
        httpretty.POST,
        artifact_url_pattern)
    httpretty.register_uri(
        httpretty.POST,
        datasets_url_pattern)

    client = GiskardClient(url, token)

    saved_id = diabetes_dataset_with_target.save(client, "test-project")
    assert re.match("^[a-z0-9]{32}$", saved_id)

    artifact_requests = [i for i in httpretty.latest_requests() if artifact_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0

    artifact_requests = [i for i in httpretty.latest_requests() if datasets_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0
        assert req.headers.get("Content-Type") == "application/json"

    with pytest.raises(Exception) as e:
        diabetes_dataset.save(client, "test-project")
    assert e.match("target column is not present in the dataset")

    with pytest.raises(Exception) as e:
        diabetes_dataset.column_meanings = {"test": "test"}
        diabetes_dataset.save(client, "test-project")
    assert e.match("target column is not present in the dataset")


@httpretty.activate(verbose=True, allow_net_connect=False)
def _test_upload_model(model: Model, ds: Dataset):
    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[a-z0-9]{32}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")

    httpretty.register_uri(httpretty.POST, artifact_url_pattern)
    httpretty.register_uri(httpretty.POST, models_url_pattern)

    client = GiskardClient(url, token)
    if model.is_regression:
        # Warning Scenario: classification_labels is sent for regression model
        with pytest.warns(UserWarning):
            model_id = model.save(client, 'test-project', ds)
    else:
        model_id = model.save(client, 'test-project', ds)

    assert re.match("^[a-z0-9]{32}$", model_id)

    artifact_requests = [i for i in httpretty.latest_requests() if artifact_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0

    artifact_requests = [i for i in httpretty.latest_requests() if models_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0
        assert req.headers.get("Content-Type") == "application/json"


def _test_upload_model_exceptions(model: Model, ds: Dataset):
    client = GiskardClient(url, token)

    # Error Scenario : invalid feature_names
    with pytest.raises(Exception) as e:
        Model(
            clf=model.clf,
            model_type=model.meta.model_type,
            feature_names=["some"],
            name=model_name,
            classification_labels=model.meta.classification_labels
        ).save(client, 'test-project', ds)
    assert e.match('Value mentioned in  feature_names is  not available in validate_df')

    if model.is_classification:
        # Error Scenario: Classification model sent without classification_labels
        with pytest.raises(Exception) as e:
            Model(
                clf=model.clf,
                model_type=model.meta.model_type,
                feature_names=model.meta.feature_names,
                name=model_name
            ).save(client, 'test-project', ds)
        assert e.match('Invalid classification_labels parameter: None. Please specify valid list of strings')

        # Error Scenario: Target has values not declared in Classification Label
        with pytest.raises(Exception) as e:
            Model(
                clf=model.clf,
                model_type=model.meta.model_type,
                feature_names=model.meta.feature_names,
                name=model_name,
                classification_labels=[0, 1]
            ).save(client, 'test-project', ds)
        assert e.match('Values in default column are not declared in classification_labels parameter')


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
                         [
                             ('german_credit_data', 'german_credit_model'),
                             ('diabetes_dataset', 'linear_regression_diabetes')])
def test_upload_models_exceptions(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    _test_upload_model_exceptions(model, data)
