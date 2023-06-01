import re

import httpretty
import pytest

from giskard import Dataset
from giskard import SKLearnModel
from giskard.client.giskard_client import GiskardClient

import tests.utils

url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "application/json"
model_name = "uploaded model"
b_content_type = b"application/json"


@httpretty.activate(verbose=True, allow_net_connect=False)
def test_upload_df(diabetes_dataset: Dataset, diabetes_dataset_with_target: Dataset):
    artifact_url_pattern = re.compile(
        r"http://giskard-host:12345/api/v2/artifacts/test-project/datasets/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[data.csv.zst|giskard\-dataset\-meta.yaml]")
    datasets_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/datasets")

    httpretty.register_uri(
        httpretty.POST,
        artifact_url_pattern)
    httpretty.register_uri(
        httpretty.POST,
        datasets_url_pattern)

    client = GiskardClient(url, token)

    saved_id = diabetes_dataset_with_target.save(client, "test-project")
    tests.utils.match_model_id(saved_id)
    tests.utils.match_url_patterns(httpretty.latest_requests(), artifact_url_pattern)
    tests.utils.match_url_patterns(httpretty.latest_requests(), datasets_url_pattern)

    with pytest.raises(Exception) as e:
        diabetes_dataset.save(client, "test-project")
    assert e.match("target column is not present in the dataset")

    with pytest.raises(Exception) as e:
        diabetes_dataset.feature_types = {"test": "test"}
        diabetes_dataset.save(client, "test-project")
    assert e.match("target column is not present in the dataset")


@httpretty.activate(verbose=True, allow_net_connect=False)
def _test_upload_model(model: SKLearnModel, ds: Dataset):
    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")

    httpretty.register_uri(httpretty.POST, artifact_url_pattern)
    httpretty.register_uri(httpretty.POST, models_url_pattern)

    client = GiskardClient(url, token)
    if model.is_regression:
        # Warning Scenario: classification_labels is sent for regression model
        with pytest.warns(UserWarning):
            model.upload(client, 'test-project', ds)
    else:
        model.upload(client, 'test-project', ds)

    tests.utils.match_model_id(model.id)
    tests.utils.match_url_patterns(httpretty.latest_requests(), artifact_url_pattern)
    tests.utils.match_url_patterns(httpretty.latest_requests(), models_url_pattern)


def _test_upload_model_exceptions(model: SKLearnModel, ds: Dataset):
    client = GiskardClient(url, token)

    # Error Scenario : invalid feature_names
    with pytest.raises(Exception) as e:
        SKLearnModel(
            clf=model.clf,
            model_type=model.meta.model_type,
            feature_names=["some"],
            name=model_name,
            classification_labels=model.meta.classification_labels
        ).upload(client, 'test-project', ds)
    assert e.match('Value mentioned in  feature_names is  not available in validate_df')

    if model.is_classification:
        # Error Scenario: Target has values not declared in Classification Label
        with pytest.raises(Exception) as e:
            SKLearnModel(
                clf=model.clf,
                model_type=model.meta.model_type,
                feature_names=model.meta.feature_names,
                name=model_name,
                classification_labels=[0, 1]
            ).upload(client, 'test-project', ds)
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
