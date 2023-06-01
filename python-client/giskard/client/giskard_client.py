"""API Client to interact with the Giskard app"""
import logging
import os
import posixpath
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from mlflow.store.artifact.artifact_repo import verify_artifact_path
from mlflow.utils.file_utils import relative_path_to_artifact_path
from mlflow.utils.rest_utils import augmented_raise_for_status
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests_toolbelt import sessions

import giskard
from giskard.client.analytics_collector import GiskardAnalyticsCollector, anonymize
from giskard.client.dtos import TestSuiteNewDTO
from giskard.client.project import Project
from giskard.client.python_utils import warning
from giskard.core.core import ModelMeta, DatasetMeta
from giskard.core.core import SupportedModelTypes

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
            self.analytics.init(server_settings)
        except Exception:
            logger.warning(f"Failed to fetch server settings", exc_info=True)
        self.analytics.track("Init GiskardClient", {"client version": giskard.__version__})

    @property
    def session(self):
        return self._session

    def list_projects(self) -> List[Project]:
        self.analytics.track("List Projects")
        response = self._session.get("projects").json()
        return [Project(self._session, p["key"], p["id"], analytics=self.analytics) for p in response]

    def get_project(self, project_key: str):
        """
        Function to get the project that belongs to the mentioned project key
        Args:
            project_key:
                The unique value of  project provided during project creation
        Returns:
            Project:
                The giskard project that belongs to the project key
        """
        self.analytics.track("Get Project", {"project_key": anonymize(project_key)})
        response = self._session.get(f"project", params={"key": project_key}).json()
        return Project(self._session, response["key"], response["id"], analytics=self.analytics)

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
            Project:
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
        return Project(self._session, actual_project_key, actual_project_id, analytics=self.analytics)

    def load_model_meta(self, project_key: str, uuid: str) -> ModelMeta:
        res = self._session.get(f"project/{project_key}/models/{uuid}").json()
        return ModelMeta(
            name=res['name'],
            feature_names=res['featureNames'],
            model_type=SupportedModelTypes[res['modelType']],
            classification_labels=res['classificationLabels'],
            classification_threshold=res['threshold']
        )

    def load_dataset_meta(self, project_key: str, uuid: str) -> DatasetMeta:
        res = self._session.get(f"project/{project_key}/datasets/{uuid}").json()
        return DatasetMeta(
            name=res['name'],
            target=res['target'],
            feature_types=res['featureTypes'],
            column_types=res['columnTypes'],
        )

    def save_model_meta(
            self,
            project_key: str,
            model_id: str,
            meta: ModelMeta,
            python_version: str,
            size: int
    ):
        self._session.post(f"project/{project_key}/models", json={
            "languageVersion": python_version,
            "language": "PYTHON",
            "modelType": meta.model_type.name.upper(),
            "threshold": meta.classification_threshold,
            "featureNames": meta.feature_names,
            "classificationLabels": meta.classification_labels,
            "id": model_id,
            "project": project_key,
            "name": meta.name,
            "size": size
        })
        self.analytics.track(
            "Upload Model",
            {
                "name": anonymize(meta.name),
                "projectKey": anonymize(project_key),
                "languageVersion": python_version,
                "modelType": meta.model_type,
                "threshold": meta.classification_threshold,
                "featureNames": anonymize(meta.feature_names),
                "language": "PYTHON",
                "classificationLabels": anonymize(meta.classification_labels),
                "size": size,
            },
        )

        print(
            f"Model successfully uploaded to project key '{project_key}' with ID = {model_id}"
        )

    def log_artifacts(self, local_dir, artifact_path=None):
        local_dir = os.path.abspath(local_dir)
        for root, _, filenames in os.walk(local_dir):
            if root == local_dir:
                artifact_dir = artifact_path
            else:
                rel_path = os.path.relpath(root, local_dir)
                rel_path = relative_path_to_artifact_path(rel_path)
                artifact_dir = (
                    posixpath.join(artifact_path, rel_path) if artifact_path else rel_path
                )
            for f in filenames:
                self.log_artifact(os.path.join(root, f), artifact_dir)

    def load_artifact(self, local_file: Path, artifact_path: str = None):
        if local_file.exists():
            logger.info(f"Artifact {artifact_path} already exists, skipping download")
            return

        files = self._session.get("artifact-info/" + artifact_path)
        augmented_raise_for_status(files)

        for f in files.json():
            destination_file = (local_file / f)
            destination_file.parent.mkdir(exist_ok=True, parents=True)
            if destination_file.exists():
                continue
            file_path = posixpath.join("/", artifact_path, f)
            resp = self._session.get(f"artifacts{file_path}", stream=True)
            augmented_raise_for_status(resp)

            with open(destination_file, "wb") as out:
                chunk_size = 1024 * 1024  # 1 MB
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    out.write(chunk)

    def log_artifact(self, local_file, artifact_path=None):
        verify_artifact_path(artifact_path)

        file_name = os.path.basename(local_file)

        paths = (artifact_path, file_name) if artifact_path else (file_name,)
        endpoint = "artifacts" + posixpath.join("/", *paths)
        with open(local_file, "rb") as f:
            resp = self._session.post(endpoint, data=f)
            augmented_raise_for_status(resp)

    def save_dataset_meta(self, project_key, dataset_id, meta: DatasetMeta, original_size_bytes, compressed_size_bytes):
        self._session.post(f"project/{project_key}/datasets", json={
            "project": project_key,
            "id": dataset_id,
            "name": meta.name,
            "target": meta.target,
            "featureTypes": meta.feature_types,
            "columnTypes": meta.column_types,
            "originalSizeBytes": original_size_bytes,
            "compressedSizeBytes": compressed_size_bytes
        })
        self.analytics.track(
            "Upload Dataset",
            {
                "project": anonymize(project_key),
                "id": anonymize(dataset_id),
                "name": anonymize(meta.name),
                "target": anonymize(meta.target),
                "featureTypes": anonymize(meta.feature_types),
                "columnTypes": anonymize(meta.column_types),
                "original_size_bytes": original_size_bytes,
                "compressed_size_bytes": compressed_size_bytes
            },
        )

        print(
            f"Dataset successfully uploaded to project key '{project_key}' with ID = {dataset_id}"
        )

    def get_server_info(self):
        return self._session.get("settings").json()

    def save_test_suite(self, dto: TestSuiteNewDTO):
        return self._session.post(f"testing/project/{dto.project_key}/suites-new", json=dto.dict()).json()
