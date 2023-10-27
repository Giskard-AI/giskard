import glob
import logging
import os
import re
import tarfile
from pathlib import Path
from typing import Optional

import requests
import requests_mock
from giskard.ml_worker.core.savable import Artifact

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
