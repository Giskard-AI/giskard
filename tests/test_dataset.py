import pandas as pd
import numpy as np
from pydantic import ValidationError
import pytest
import uuid

import requests_mock

from giskard.datasets.base import Dataset
from giskard.core.dataset_validation import validate_optional_target
from giskard.client.dtos import DatasetMetaInfo

from tests import utils
from tests.communications.test_dto_serialization import is_required, get_fields, get_name


# FIXME: conflict on `name` between Giskard Hub (@NotBlank) and Python client (optional in DatasetMeta and DatasetMetaInfo)
MANDATORY_FIELDS = [
    "id",
    "originalSizeBytes",
    "numberOfRows",
    "columnTypes",
    "columnDtypes",
    "compressedSizeBytes",
    "categoryFeatures",
    "createdDate",
]
OPTIONAL_FIELDS = [
    "name",
    "target",
]

valid_df = pd.DataFrame(
    {
        "categorical_column": ["turtle", "crocodile", "turtle"],
        "text_column": ["named Giskard", "a nile crocodile", "etc"],
        "numeric_column": [15.5, 25.9, 2.4],
    }
)
valid_df_column_types = {
    "categorical_column": "category",
    "text_column": "text",
    "numeric_column": "numeric",
}

nonvalid_df = pd.DataFrame(
    {
        "categorical_column": [["turtle"], ["crocodile"], ["turtle"]],
        "text_column": [{1: "named Giskard"}, {2: "a nile crocodile"}, {3: "etc"}],
        "numeric_column": [(15.5, 1), (25.9, 2), (2.4, 3)],
    }
)


def test_factory():
    my_dataset = Dataset(valid_df)
    assert isinstance(my_dataset, Dataset)


def test_valid_df_column_types():
    # Option 0: none of column_types, cat_columns, infer_column_types = True are provided
    with pytest.warns(
        UserWarning,
        match=r"You did not provide the optional argument 'target'\. 'target' is the column name "
        r"in df corresponding to the actual target variable \(ground truth\)\.",
    ):
        my_dataset = Dataset(valid_df)
        validate_optional_target(my_dataset)
    assert my_dataset.column_types == {
        "categorical_column": "category",
        "text_column": "text",
        "numeric_column": "numeric",
    }

    # Option 1: column_types is provided
    my_dataset = Dataset(valid_df, column_types=valid_df_column_types)
    assert my_dataset.column_types == valid_df_column_types

    # Option 2: cat_columns is provided
    cat_columns = ["categorical_column"]
    my_dataset = Dataset(valid_df, cat_columns=cat_columns)
    assert my_dataset.column_types == valid_df_column_types

    # Option 3: infer_column_types is provided
    my_dataset = Dataset(valid_df)
    assert my_dataset.column_types == valid_df_column_types


def test_nonvalid_df_column_types():
    # Option 0: none of column_types, cat_columns, infer_column_types = True are provided
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df)

    # Option 1: column_types is provided
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df, column_types=valid_df_column_types)

    # Option 2: cat_columns is provided
    cat_columns = ["categorical_column"]
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df, cat_columns=cat_columns)

    # Option 3: infer_column_types is provided
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df)


def test_dataset_raises_exception_if_mixed_column_types():
    df = pd.DataFrame({"feature": [1, 2, "string", None, np.nan], "target": [0, 0, 1, 1, 0]})

    with pytest.raises(TypeError):
        Dataset(df, target="target")


def test_inference_priority():
    column_types = {"categorical_column": "text"}
    expected_df_column_types = {
        "categorical_column": "text",
        "text_column": "text",
        "numeric_column": "numeric",
    }

    # Case 1: only one column in column_types is provided
    my_dataset = Dataset(valid_df, column_types=column_types)
    assert my_dataset.column_types == expected_df_column_types

    # Case 2: one column in column_types is provided, one in cat_columns
    my_dataset = Dataset(valid_df, column_types=column_types, cat_columns=["categorical_column"])
    assert my_dataset.column_types == valid_df_column_types

    # Case 3: an unknown column in column_types is provided
    column_types = {"unknown_column": "text"}
    my_dataset = Dataset(valid_df, column_types=column_types, cat_columns=["categorical_column"])
    assert my_dataset.column_types == valid_df_column_types


def test_numeric_column_names():
    df = pd.DataFrame(np.ones((10, 3)), columns=[1, 2, 3])

    assert Dataset(df, target=2)
    assert Dataset(df, column_types={1: "numeric"})


def test_infer_column_types():

    # if df_size >= 100     ==> category_threshold = floor(log10(df_size))
    assert Dataset(pd.DataFrame({"f": [1, 2] * 50})).column_types["f"] == "category"
    assert Dataset(pd.DataFrame({"f": ["a", "b"] * 50})).column_types["f"] == "category"
    assert Dataset(pd.DataFrame({"f": ["a", "b"] * 49})).column_types["f"] == "category"
    assert Dataset(pd.DataFrame({"f": [1, 2, 3] * 50})).column_types["f"] == "numeric"
    assert Dataset(pd.DataFrame({"f": ["a", "b", "c"] * 50})).column_types["f"] == "text"

    # if 2 < df_size < 100  ==> category_threshold = 2
    assert Dataset(pd.DataFrame({"f": [1, 2, 1]})).column_types["f"] == "category"
    assert Dataset(pd.DataFrame({"f": ["a", "b", "a"]})).column_types["f"] == "category"
    assert Dataset(pd.DataFrame({"f": [1, 2, 3]})).column_types["f"] == "numeric"
    assert Dataset(pd.DataFrame({"f": ["a", "b", "c"]})).column_types["f"] == "text"

    # if df_size <= 2       ==> category_threshold = 0 (column is text)
    assert Dataset(pd.DataFrame({"f": [1, 2]})).column_types["f"] == "numeric"
    assert Dataset(pd.DataFrame({"f": ["a", "b"]})).column_types["f"] == "text"
    assert Dataset(pd.DataFrame({"f": [1]})).column_types["f"] == "numeric"
    assert Dataset(pd.DataFrame({"f": ["a"]})).column_types["f"] == "text"


def test_dataset_download_with_cache(request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        # Save the dataset to cache dir
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key=project_key)

        with utils.MockedClient(mock_all=False) as (client, mr):
            # The dataset can be then loaded from the cache, without further requests
            requested_urls = []
            requested_urls.extend(utils.register_uri_for_dataset_meta_info(mr, dataset, project_key))

            downloaded_dataset = Dataset.download(client=client, project_key=project_key, dataset_id=str(dataset.id))

            for requested_url in requested_urls:
                assert utils.is_url_requested(mr.request_history, requested_url)

            assert downloaded_dataset.id == dataset.id
            assert downloaded_dataset.meta == dataset.meta


def test_dataset_download(request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        with utils.MockedClient(mock_all=False) as (client, mr):
            # The dataset needs to request files
            requested_urls = []
            requested_urls.extend(utils.register_uri_for_dataset_meta_info(mr, dataset, project_key))
            requested_urls.extend(
                utils.register_uri_for_dataset_artifact_info(mr, dataset, project_key, register_file_contents=True)
            )

            downloaded_dataset = Dataset.download(client=client, project_key=project_key, dataset_id=str(dataset.id))

            for requested_url in requested_urls:
                assert utils.is_url_requested(mr.request_history, requested_url)

            assert downloaded_dataset.id == dataset.id
            assert downloaded_dataset.meta == dataset.meta


def test_dataset_meta_info():
    klass = DatasetMetaInfo
    mandatory_field_names = []
    optional_field_names = []
    for name, field in get_fields(klass).items():
        mandatory_field_names.append(get_name(name, field)) if is_required(field) else \
            optional_field_names.append(get_name(name, field))
    assert set(mandatory_field_names) == set(MANDATORY_FIELDS)
    assert set(optional_field_names) == set(OPTIONAL_FIELDS)


def test_fetch_dataset_meta(request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    project_key = str(uuid.uuid4())

    for op in OPTIONAL_FIELDS:
        with utils.MockedClient(mock_all=False) as (client, mr):
            meta_info = utils.mock_dataset_meta_info(dataset, project_key)
            meta_info.pop(op)
            mr.register_uri(method=requests_mock.GET, url=utils.get_url_for_dataset(dataset, project_key), json=meta_info)

            # Should not raise
            client.load_dataset_meta(project_key, uuid=str(dataset.id))

    for op in MANDATORY_FIELDS:
        with utils.MockedClient(mock_all=False) as (client, mr):
            meta_info = utils.mock_dataset_meta_info(dataset, project_key)
            meta_info.pop(op)
            mr.register_uri(method=requests_mock.GET, url=utils.get_url_for_dataset(dataset, project_key), json=meta_info)

            # Should raise due to missing of values
            with pytest.raises(ValidationError):
                client.load_dataset_meta(project_key, uuid=str(dataset.id))
