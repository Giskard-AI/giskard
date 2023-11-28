### Test giskard_client.py
# Path: tests/core/test_giskard_client.py
import pytest
from giskard.client.giskard_client import GiskardClient
from giskard.client.giskard_client import explain_error
from requests import Response
import requests_mock


def test_init_giskard_client_with_wrong_api_key():
    """
    Test giskard client with wrong api key
    """
    url = "http://giskard-host:9000"
    api_key = "<wrong api key>"
    mocked_requests = requests_mock.Mocker()
    mocked_requests.__enter__()
    mocked_requests.register_uri(requests_mock.GET, url, json={})
    mocked_requests.register_uri(requests_mock.GET, f"{url}/public-api/ml-worker-connect", status_code=401)

    with pytest.raises(Exception) as exc_info:
        GiskardClient(url, api_key)
    print(exc_info)
    assert "Not authorized to access this resource. Please check your API key" in str(exc_info)


def test_explain_error_raw():
    """
    Test explain error when the response is not from the adapter
    """
    response401 = Response()
    response401.status_code = 401
    with pytest.raises(Exception) as exc_info:
        raise explain_error(response401)
    assert "Not authorized to access this resource. Please check your API key" in str(exc_info)

    response403 = Response()
    response403.status_code = 403
    with pytest.raises(Exception) as exc_info:
        raise explain_error(response403)
    assert "Access denied. Please check your permissions." in str(exc_info)
