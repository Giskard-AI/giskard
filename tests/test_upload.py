import re

import pytest

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests.utils import MockedClient, match_model_id, match_url_patterns

model_name = "uploaded model"


def test_upload_df(diabetes_dataset: Dataset, diabetes_dataset_with_target: Dataset):
    artifact_url_pattern = re.compile(
        r"http://giskard-host:12345/api/v2/artifacts/test-project/datasets/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[data.csv.zst|giskard\-dataset\-meta.yaml]"
    )
    datasets_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/datasets")

    with MockedClient() as (client, mr):
        saved_id = diabetes_dataset_with_target.upload(client, "test-project")
        match_model_id(saved_id)
        match_url_patterns(mr.request_history, artifact_url_pattern)
        match_url_patterns(mr.request_history, datasets_url_pattern)

        with pytest.raises(Exception) as e:
            Dataset(
                df=diabetes_dataset.df,
                column_types=diabetes_dataset.column_types,
                target=diabetes_dataset_with_target.target,
            )
        assert e.match(
            "Invalid target parameter: 'target' column is not present in the dataset "
            "with columns: \['age', 'sex', 'bmi', 'bp', 's1', 's2', 's3', 's4', 's5', 's6'\]"
        )  # noqa

        with pytest.raises(Exception) as e:
            diabetes_dataset.column_types = {"test": "test"}
            Dataset(
                df=diabetes_dataset.df,
                column_types=diabetes_dataset.column_types,
                target=diabetes_dataset_with_target.target,
            )
        assert e.match(
            "Invalid target parameter: 'target' column is not present in the dataset "
            "with columns: \['age', 'sex', 'bmi', 'bp', 's1', 's2', 's3', 's4', 's5', 's6'\]"
        )  # noqa


def _test_upload_model(model: SKLearnModel, ds: Dataset):
    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    with MockedClient() as (client, mr):
        if model.is_regression:
            # Warning Scenario: classification_labels is sent for regression model
            with pytest.warns(UserWarning):
                model.upload(client, "test-project", ds)
        else:
            model.upload(client, "test-project", ds)

        match_model_id(model.id)
        match_url_patterns(mr.request_history, artifact_url_pattern)
        match_url_patterns(mr.request_history, models_url_pattern)


def _test_upload_model_exceptions(model: SKLearnModel, ds: Dataset):
    with MockedClient() as (client, mr):
        # Error Scenario : invalid feature_names
        with pytest.raises(Exception) as e:
            SKLearnModel(
                model=model.model,
                model_type=model.meta.model_type,
                feature_names=["some"],
                name=model_name,
                classification_labels=model.meta.classification_labels,
            ).upload(client, "test-project", ds)
        assert e.match("Value mentioned in feature_names is not available in validate_df")

        if model.is_classification:
            # Error Scenario: Target has values not declared in Classification Label
            with pytest.raises(Exception) as e:
                SKLearnModel(
                    model=model.model,
                    model_type=model.meta.model_type,
                    feature_names=model.meta.feature_names,
                    name=model_name,
                    classification_labels=[0, 1],
                ).upload(client, "test-project", ds)
            assert e.match(
                "Values .* in .* column are not declared in classification_labels parameter .* of the model: uploaded model"
            )  # noqa


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


@pytest.mark.parametrize(
    "data,model,", [("german_credit_data", "german_credit_model"), ("diabetes_dataset", "linear_regression_diabetes")]
)
def test_upload_models_exceptions(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    _test_upload_model_exceptions(model, data)
