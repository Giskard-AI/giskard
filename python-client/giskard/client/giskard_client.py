"""API Client to interact with the Giskard app"""
import logging
from typing import List
from urllib.parse import urljoin

from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests_toolbelt import sessions

import giskard
from giskard.client.analytics_collector import GiskardAnalyticsCollector, anonymize
from giskard.client.project import GiskardProject
from giskard.client.python_utils import warning

logger = logging.getLogger(__name__)


class GiskardError(Exception):
    def __init__(self, message: str, status: int, code: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def explain_error(err_resp):
    status = err_resp.get("status")
    code = err_resp.get("message")
    message = None
    if status == 401:
        message = "Access token is invalid or expired. Please generate a new one"

    if message is None:
        message = f"{err_resp.get('title', 'Unknown error')}: {err_resp.get('detail', 'no details')}"
    return GiskardError(status=status, code=code, message=message)


class ErrorHandlingAdapter(HTTPAdapter):
    def build_response(self, req, resp):
        response = super().build_response(req, resp)

        if not response.ok:
            giskard_error = None
            try:
                err_resp = response.json()

                giskard_error = explain_error(err_resp)
            except:  # NOSONAR
                response.raise_for_status()
            raise giskard_error
        return response


class BearerAuth(AuthBase):
    """Defines bearer authentication token as Authorization header"""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = f"Bearer {self.token}"
        return r


class GiskardClient:
    def __init__(self, url: str, token: str):
        base_url = urljoin(url, "/api/v2/")
        self._session = sessions.BaseUrlSession(base_url=base_url)
        self._session.mount(base_url, ErrorHandlingAdapter())
        self._session.auth = BearerAuth(token)
        self.analytics = GiskardAnalyticsCollector()
        try:
            server_settings = self._session.get("settings").json()
            self.analytics. \
                init(server_settings)
        except Exception:
            logger.warning(f"Failed to fetch server settings", exc_info=True)
        self.analytics.track("Init GiskardClient", {"client version": giskard.__version__})

    @property
    def session(self):
        return self._session

    def list_projects(self) -> List[GiskardProject]:
        self.analytics.track("List Projects")
        response = self._session.get("projects").json()
        return [GiskardProject(self._session, p["key"], p["id"], analytics=self.analytics) for p in response]

    def get_project(self, project_key: str):
        """
        Function to get the project that belongs to the mentioned project key
        Args:
            project_key:
                The unique value of  project provided during project creation
        Returns:
            GiskardProject:
                The giskard project that belongs to the project key
        """
        self.analytics.track("Get Project", {"project_key": anonymize(project_key)})
        response = self._session.get(f"project", params={"key": project_key}).json()
        return GiskardProject(self._session, response["key"], response["id"], analytics=self.analytics)

    def create_project(self, project_key: str, name: str, description: str = None):
        """
        Function to create a project in Giskard
        Args:
            project_key:
                The unique value of the project which will be used to identify  and fetch teh project in future
            name:
                The name of the project
            description:
                Describe your project
        Returns:
            GiskardProject:
                The project created in giskard
        """
        self.analytics.track(
            "Create Project",
            {
                "project_key": anonymize(project_key),
                "description": anonymize(description),
                "name": anonymize(name),
            },
        )
        try:
            response = self._session.post(
                "project", json={"description": description, "key": project_key, "name": name}
            ).json()
        except GiskardError as e:
            if e.code == "error.http.409":
                warning(
                    "This project key already exists. "
                    "If you want to reuse existing project use get_project(“project_key”) instead"
                )
            raise e
        actual_project_key = response.get("key")
        actual_project_id = response.get("id")
        if actual_project_key != project_key:
            print(f"Project created with a key : {actual_project_key}")
        return GiskardProject(self._session, actual_project_key, actual_project_id, analytics=self.analytics)
