### Test giskard_client.py
# Path: tests/core/test_giskard_client.py
import pytest
from giskard.client.giskard_client import GiskardClient, GiskardError
from giskard.client.giskard_client import explain_error
from requests import Response
import requests_mock

UNKNOWN_ERROR = "Unknown error"


def test_init_giskard_client_with_wrong_api_key():
    """
    Test giskard client with wrong api key
    """
    url = "http://giskard-host:9000"
    api_key = "<wrong api key>"
    with requests_mock.Mocker() as mocked_requests:
        mocked_requests.register_uri(requests_mock.GET, url, json={})
        mocked_requests.register_uri(requests_mock.GET, f"{url}/public-api/ml-worker-connect", status_code=401)

        with pytest.raises(Exception) as exc_info:
            GiskardClient(url, api_key)

        assert isinstance(exc_info.value, GiskardError)
        assert "Not authorized to access this resource. Please check your API key" in exc_info.value.message


def test_explain_error_raw():
    """
    Test explain error when the response is not from the adapter
    """
    response401 = Response()
    response401.status_code = 401
    exc_info = explain_error(response401)
    assert isinstance(exc_info, GiskardError)
    assert "Not authorized to access this resource. Please check your API key" in exc_info.message

    response403 = Response()
    response403.status_code = 403
    exc_info = explain_error(response403)
    assert isinstance(exc_info, GiskardError)
    assert "Access denied. Please check your permissions." in exc_info.message


def test_explain_error_generic():
    response500 = Response()
    response500.status_code = 500
    response500.title = UNKNOWN_ERROR
    response500.detail = UNKNOWN_ERROR
    exc_info = explain_error(response500)
    assert isinstance(exc_info, GiskardError)
    assert UNKNOWN_ERROR in exc_info.message

    response500 = Response()
    response500.status_code = 500
    exc_info = explain_error(response500)
    assert isinstance(exc_info, GiskardError)
    assert "No details or messages available" in exc_info.message
