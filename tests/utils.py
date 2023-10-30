import glob
import logging
import os
import re
import shutil
import tarfile
from pathlib import Path
from typing import Optional
import posixpath
import tempfile
import platform

import requests
import requests_mock
from giskard.ml_worker.core.savable import Artifact
from giskard.ml_worker.utils.file_utils import get_file_name
from giskard.path_utils import get_size

import tests.utils
from giskard.client.giskard_client import GiskardClient
from giskard.datasets.base import Dataset
from giskard.ml_worker import ml_worker
from giskard.models.base.model import BaseModel
from giskard.settings import settings

logger = logging.getLogger(__name__)
resource_dir: Path = Path.home() / ".giskard"

headers_to_match = {"Authorization": "Bearer SECRET_TOKEN", "Content-Type": "application/json"}

CALLABLE_FUNCTION_PKL_CACHE = "data.pkl"
CALLABLE_FUNCTION_META_CACHE = "meta.yaml"

CLIENT_BASE_URL = "http://giskard-host:12345/api/v2"


def match_model_id(my_model_id):
    assert re.match("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", str(my_model_id))


def match_url_patterns(last_requests, url_pattern):
    artifact_requests = [i for i in last_requests if url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert int(req.headers.get("Content-Length")) > 0
        for header_name in headers_to_match.keys():
            if header_name in dict(req.headers).keys():
                assert req.headers.get(header_name) == headers_to_match[header_name]


class MockedClient:
    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")
    ml_worker_connect_url_pattern = re.compile("http://giskard-host:12345/public-api/ml-worker-connect")

    mocked_requests: requests_mock.Mocker = None
    client: GiskardClient = None
    mock_all: bool

    def __init__(self, mock_all=True) -> None:
        self.mock_all = mock_all

    def __enter__(self):
        self.mocked_requests = requests_mock.Mocker()
        self.mocked_requests.__enter__()
        if self.mock_all:
            api_pattern = re.compile(r"http://giskard-host:12345/api/v2/.*")

            self.mocked_requests.register_uri(requests_mock.GET, api_pattern, json={})
            self.mocked_requests.register_uri(requests_mock.POST, api_pattern, json={})
            self.mocked_requests.register_uri(requests_mock.PUT, api_pattern, json={})

        self.mocked_requests.register_uri(
            requests_mock.GET,
            "http://giskard-host:12345/api/v2/project?key=test_project",
            json={"key": "test_project", "id": 1},
        )
        self.mocked_requests.register_uri(
            requests_mock.GET,
            self.ml_worker_connect_url_pattern,
            json={},
        )

        url = "http://giskard-host:12345"
        key = "SECRET_TOKEN"
        return GiskardClient(url, key), self.mocked_requests

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mocked_requests:
            self.mocked_requests.__exit__(exc_type, exc_val, exc_tb)


def verify_model_upload(my_model, my_data):
    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")
    ml_worker_connect_url_pattern = re.compile("http://giskard-host:12345/public-api/ml-worker-connect")

    with requests_mock.Mocker() as m:
        m.register_uri(requests_mock.POST, artifact_url_pattern)
        m.register_uri(requests_mock.POST, models_url_pattern)
        m.register_uri(requests_mock.GET, settings_url_pattern)
        m.register_uri(
            requests_mock.GET,
            ml_worker_connect_url_pattern,
            json={},
        )

        url = "http://giskard-host:12345"
        key = "SECRET_TOKEN"
        client = GiskardClient(url, key)
        my_model.upload(client, "test-project", my_data)

        tests.utils.match_model_id(my_model.id)
        tests.utils.match_url_patterns(m.request_history, artifact_url_pattern)
        tests.utils.match_url_patterns(m.request_history, models_url_pattern)


def get_email_files():
    out_path = Path.home() / ".giskard"
    enron_path = out_path / "enron_with_categories"
    if not enron_path.exists():
        url = "http://bailando.sims.berkeley.edu/enron/enron_with_categories.tar.gz"
        logger.info(f"Downloading test data from: {url}")
        response = requests.get(url, stream=True)
        file = tarfile.open(fileobj=response.raw, mode="r|gz")
        os.makedirs(out_path, exist_ok=True)
        file.extractall(path=out_path)
    return [f.replace(".cats", "") for f in glob.glob(str(enron_path) + "/*/*.cats")]


class MockedWebSocketMLWorker:
    def __init__(self, is_server=False, backend_url= None, api_key=None, hf_token=None) -> None:
        client = None if is_server else MockedClient(mock_all=True)
        self.client = client

        self.backend_url = backend_url
        self.api_key = api_key
        self.hf_token = hf_token

        self.ml_worker_id = ml_worker.INTERNAL_WORKER_ID if is_server else ml_worker.EXTERNAL_WORKER_ID

    def is_remote_worker(self):
        return self.ml_worker_id is not ml_worker.INTERNAL_WORKER_ID


class MockedProjectCacheDir:
    def __init__(self, project_key=None):
        self.local_path_root = get_local_cache_project(project_key)

    def __enter__(self):
        self.local_path_root.mkdir(parents=True)
        return self.local_path_root

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(str(self.local_path_root), ignore_errors=True)


def get_local_cache_base():
    return settings.home_dir / settings.cache_dir


def get_local_cache_project(project_key: Optional[str]):
    return get_local_cache_base() / (project_key or "global")


def get_local_cache_artifact(project_key: Optional[str], name: str, uuid: str):
    return get_local_cache_project(project_key) / name / uuid


def get_local_cache_callable_artifact(project_key: Optional[str], artifact: Artifact):
    return get_local_cache_artifact(project_key, artifact._get_name(), artifact.meta.uuid)


def local_save_model_under_giskard_home_cache(model: BaseModel, project_key: str):
    local_path_model = get_local_cache_artifact(project_key, "models", str(model.id))
    local_path_model.mkdir(parents=True)
    model.save(local_path=local_path_model)


def local_save_dataset_under_giskard_home_cache(dataset: Dataset, project_key: str):
    local_path_dataset = get_local_cache_artifact(project_key, "datasets", str(dataset.id))
    local_path_dataset.mkdir(parents=True)
    dataset.save(local_path=local_path_dataset, dataset_id=dataset.id)


def local_save_artifact_under_giskard_home_cache(artifact: Artifact, project_key: Optional[str]):
    local_path = get_local_cache_callable_artifact(project_key, artifact)
    local_path.mkdir(parents=True)
    artifact.save(local_dir=local_path)


def fixup_mocked_artifact_meta_version(meta_info):
    meta_info.update({
        "displayName": meta_info.pop("display_name"),
        "moduleDoc": meta_info.pop("module_doc"),
        "version": 1,
    })
    for arg in meta_info["args"] if meta_info["args"] else []:
        arg.update({
            "defaultValue": arg.pop("default")
        })
    return meta_info


def mock_dataset_meta_info(dataset: Dataset):
    dataset_meta_info = dataset.meta.__dict__.copy()
    dataset_meta_info.update({
        "columnTypes": dataset_meta_info.pop("column_types"),
        "columnDtypes": dataset_meta_info.pop("column_dtypes"),
        "numberOfRows": dataset_meta_info.pop("number_of_rows"),
        "categoryFeatures": dataset_meta_info.pop("category_features"),
    })
    return dataset_meta_info


def mock_model_meta_info(model: BaseModel, project_key: str):
    size = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        model.save(tmpdir)
        size = get_size(tmpdir)
    meta = model.meta
    model_meta_info = meta.__dict__.copy()
    model_meta_info.update({
        "threshold": model_meta_info.pop("classification_threshold"),
        "modelType": model_meta_info.pop("model_type").name.upper(),
        "featureNames": model_meta_info.pop("feature_names"),
        "classificationLabels": model_meta_info.pop("classification_labels"),
        "classificationLabelsDtype": (
            None
            if (not meta.classification_labels or not len(meta.classification_labels))
            else type(meta.classification_labels[0]).__name__
        ),
        "languageVersion": platform.python_version(),
        "language": "PYTHON",
        "id": str(model.id),
        "project": project_key,
        "size": size,
    })
    return model_meta_info


def register_uri_for_artifact_meta_info(mr: requests_mock.Mocker, cf: Artifact, project_key:Optional[str] = None):
    url = posixpath.join(CLIENT_BASE_URL, "project", project_key, cf._get_name(), cf.meta.uuid) if project_key \
        else posixpath.join(CLIENT_BASE_URL, cf._get_name(), cf.meta.uuid)
    # Fixup the differences from Backend
    meta_info = fixup_mocked_artifact_meta_version(cf.meta.to_json())

    mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)


def register_uri_for_artifact_info(mr: requests_mock.Mocker, cf: Artifact, project_key:Optional[str] = None):
    artifact_info_url = posixpath.join(CLIENT_BASE_URL, "artifact-info", project_key, cf._get_name(), cf.meta.uuid) if project_key \
        else posixpath.join(CLIENT_BASE_URL, "artifact-info", "global", cf._get_name(), cf.meta.uuid)
    artifacts = [
        CALLABLE_FUNCTION_PKL_CACHE,
        CALLABLE_FUNCTION_META_CACHE,
    ]
    mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)


def register_uri_for_artifacts_under_dir(mr: requests_mock.Mocker, dir_path: Path, artifacts_base_url, register_file_contents: bool = False):
    artifacts = []
    for f in dir_path.iterdir():
        artifacts.append(f.name)
        if register_file_contents:
            with f.open("rb") as content:
                # Read the entire file can use a lot of memory
                mr.register_uri(method=requests_mock.GET, url=posixpath.join(artifacts_base_url, f.name), content=content.read())
    return artifacts


def register_uri_for_dataset_meta_info(mr: requests_mock.Mocker, dataset: Dataset, project_key: str):
    dataset_url = posixpath.join(CLIENT_BASE_URL, "project", project_key, "datasets", str(dataset.id))
    dataset_meta_info = mock_dataset_meta_info(dataset)
    mr.register_uri(method=requests_mock.GET, url=dataset_url, json=dataset_meta_info)


def register_uri_for_dataset_artifact_info(mr: requests_mock.Mocker, dataset: Dataset, project_key: str, register_file_contents: bool = False):
    artifact_info_url = posixpath.join(CLIENT_BASE_URL, "artifact-info", project_key, "datasets", str(dataset.id))
    artifacts_base_url = posixpath.join(CLIENT_BASE_URL, "artifacts", project_key, "datasets", str(dataset.id))
    artifacts = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        dataset.save(Path(tmpdir), dataset.id)  # Save dataset in temp dir
        artifacts = register_uri_for_artifacts_under_dir(mr, tmpdir_path, artifacts_base_url, register_file_contents)

    mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)


def register_uri_for_model_meta_info(mr: requests_mock.Mocker, model: BaseModel, project_key: str):
    model_url = posixpath.join(CLIENT_BASE_URL, "project", project_key, "models", str(model.id))
    model_meta_info = mock_model_meta_info(model, project_key=project_key)
    mr.register_uri(method=requests_mock.GET, url=model_url, json=model_meta_info)


def register_uri_for_model_artifact_info(mr: requests_mock.Mocker, model: BaseModel, project_key: str, register_file_contents: bool = False):
    artifact_info_url = posixpath.join(CLIENT_BASE_URL, "artifact-info", project_key, "models", str(model.id))
    artifacts_base_url = posixpath.join(CLIENT_BASE_URL, "artifacts", project_key, "models", str(model.id))
    artifacts = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        model.save(Path(tmpdir))  # Save dataset in temp dir
        artifacts = register_uri_for_artifacts_under_dir(mr, tmpdir_path, artifacts_base_url, register_file_contents)

    mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)


def register_uri_for_inspection(mr: requests_mock.Mocker, project_key: str, inspection_id: int, sample: bool):
    url = posixpath.join(CLIENT_BASE_URL, "artifacts", f"{project_key}/models/inspections/{inspection_id}")
    calculated_url = posixpath.join(url, get_file_name("calculated", "csv", sample))
    predictions_url = posixpath.join(url, get_file_name("predictions", "csv", sample))
    mr.register_uri(method=requests_mock.POST, url=calculated_url, json={})
    mr.register_uri(method=requests_mock.POST, url=predictions_url, json={})
