import re
from pathlib import Path

import requests_mock

import tests.utils
from giskard.client.giskard_client import GiskardClient

resource_dir: Path = Path.home() / ".giskard"

headers_to_match = {"Authorization": "Bearer SECRET_TOKEN", "Content-Type": "application/json"}


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
    ml_worker_connect_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings/ml-worker-connect")

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
            json={
                "externalMlWorkerEntrypointPort": 40051,
                "externalMlWorkerEntrypointHost": None,
                "encryptionKey": "7J2oBM4si/GciQScXjjs6w==",
                "keyId": "fh1sjr7h",
            },
        )

        url = "http://giskard-host:12345"
        token = "SECRET_TOKEN"
        return GiskardClient(url, token), self.mocked_requests

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mocked_requests:
            self.mocked_requests.__exit__(exc_type, exc_val, exc_tb)


def verify_model_upload(my_model, my_data):
    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")
    settings_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings")
    ml_worker_connect_url_pattern = re.compile("http://giskard-host:12345/api/v2/settings/ml-worker-connect")

    with requests_mock.Mocker() as m:
        m.register_uri(requests_mock.POST, artifact_url_pattern)
        m.register_uri(requests_mock.POST, models_url_pattern)
        m.register_uri(requests_mock.GET, settings_url_pattern)
        m.register_uri(
            requests_mock.GET,
            ml_worker_connect_url_pattern,
            json={
                "externalMlWorkerEntrypointPort": 40051,
                "externalMlWorkerEntrypointHost": None,
                "encryptionKey": "7J2oBM4si/GciQScXjjs6w==",
                "keyId": "fh1sjr7h",
            },
        )

        url = "http://giskard-host:12345"
        token = "SECRET_TOKEN"
        client = GiskardClient(url, token)
        my_model.upload(client, "test-project", my_data)

        tests.utils.match_model_id(my_model.id)
        tests.utils.match_url_patterns(m.request_history, artifact_url_pattern)
        tests.utils.match_url_patterns(m.request_history, models_url_pattern)
