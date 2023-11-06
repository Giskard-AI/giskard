"""API Client to interact with the Giskard app"""
from typing import List

import logging
import os
import posixpath
from pathlib import Path
from urllib.parse import urljoin
from uuid import UUID

from mlflow.store.artifact.artifact_repo import verify_artifact_path
from mlflow.utils.file_utils import relative_path_to_artifact_path
from mlflow.utils.rest_utils import augmented_raise_for_status
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests_toolbelt import sessions

import giskard
from giskard.client.dtos import DatasetMetaInfo, ModelMetaInfo, ServerInfo, SuiteInfo, TestSuiteDTO
from giskard.client.project import Project
from giskard.client.python_utils import warning
from giskard.core.core import SMT, DatasetMeta, ModelMeta, TestFunctionMeta
from giskard.utils.analytics_collector import analytics, anonymize

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
        message = "Access key is invalid or expired. Please generate a new one"

    if message is None:
        if "title" in err_resp or err_resp.get("detail"):
            message = f"{err_resp.get('title', 'Unknown error')}: {err_resp.get('detail', 'no details')}"
        elif "message" in err_resp:
            message = err_resp["message"]
    return GiskardError(status=status, code=code, message=message)


class ErrorHandlingAdapter(HTTPAdapter):
    def build_response(self, req, resp):
        response = super().build_response(req, resp)

        if not response.ok:
            giskard_error = None
            try:
                err_resp = response.json()

                giskard_error = explain_error(err_resp)
            except:  # noqa
                response.raise_for_status()
            raise giskard_error
        return response


class BearerAuth(AuthBase):
    """Defines bearer authentication token as Authorization header"""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class GiskardClient:
    def __init__(self, url: str, key: str, hf_token: str = None):
        self.host_url = url
        self.key = key
        self.hf_token = hf_token
        base_url = urljoin(url, "/api/v2/")
        self._session = sessions.BaseUrlSession(base_url=base_url)
        self._session.mount(base_url, ErrorHandlingAdapter())
        self._session.auth = BearerAuth(key)
        if hf_token:
            self._session.cookies["spaces-jwt"] = hf_token

        server_settings: ServerInfo = self.get_server_info()

        if server_settings.serverVersion != giskard.__version__:
            warning(
                f"Your giskard client version ({giskard.__version__}) does not match the hub version "
                f"({server_settings.serverVersion}). "
                f"Please upgrade your client to the latest version. "
                f"pip install \"giskard[hub]>=2.0.0b\" -U"
            )
        analytics.init_server_info(server_settings)

        analytics.track("Init GiskardClient", {"client version": giskard.__version__})

    @property
    def session(self):
        return self._session

    def list_projects(self) -> List[Project]:
        analytics.track("List Projects")
        response = self._session.get("projects").json()
        return [Project(self._session, p["key"], p["id"]) for p in response]

    def get_project(self, project_key: str) -> Project:
        """
        Function to get the project that belongs to the mentioned project key
        Args:
            project_key:
                The unique value of  project provided during project creation
        Returns:
            Project:
                The giskard project that belongs to the project key
        """
        analytics.track("Get Project", {"project_key": anonymize(project_key)})
        response = self._session.get("project", params={"key": project_key}).json()
        return Project(self._session, response["key"], response["id"])

    def create_project(self, project_key: str, name: str, description: str = None) -> Project:
        """
        Function to create a project in Giskard
        Args:
            project_key:
                The unique value of the project which will be used to identify  and fetch the project in future
            name:
                The name of the project
            description:
                Describe your project
        Returns:
            Project:
                The project created in giskard
        """
        analytics.track(
            "Create Project",
            {
                "project_key": anonymize(project_key),
                "description": anonymize(description),
                "name": anonymize(name),
            },
        )
        try:
            response = self._session.post(
                "project",
                json={"description": description, "key": project_key, "name": name},
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
        return Project(self._session, actual_project_key, actual_project_id)

    def get_suite(self, project_id: int, suite_id: int) -> SuiteInfo:
        analytics.track("Get suite", {"suite_id": suite_id})
        return SuiteInfo.parse_obj(self._session.get(f"testing/project/{project_id}/suite/{suite_id}").json())

    def load_model_meta(self, project_key: str, uuid: str) -> ModelMetaInfo:
        res = self._session.get(f"project/{project_key}/models/{uuid}").json()
        return ModelMetaInfo.parse_obj(res)

    def load_dataset_meta(self, project_key: str, uuid: str) -> DatasetMeta:
        res = self._session.get(f"project/{project_key}/datasets/{uuid}").json()
        info = DatasetMetaInfo.parse_obj(res)  # Used for validation, and avoid extraand typos
        return DatasetMeta(
            name=info.name,
            target=info.target,
            column_types=info.columnTypes,
            column_dtypes=info.columnDtypes,
            number_of_rows=info.numberOfRows,
            category_features=info.categoryFeatures,
        )

    def save_model_meta(
        self,
        project_key: str,
        model_id: UUID,
        meta: ModelMeta,
        python_version: str,
        size: int,
    ):
        class_label_dtype = (
            None
            if (not meta.classification_labels or not len(meta.classification_labels))
            else type(meta.classification_labels[0]).__name__
        )

        self._session.post(
            f"project/{project_key}/models",
            json={
                "languageVersion": python_version,
                "language": "PYTHON",
                "modelType": meta.model_type.name.upper(),
                "threshold": meta.classification_threshold,
                "featureNames": meta.feature_names,
                "classificationLabels": meta.classification_labels,
                "classificationLabelsDtype": class_label_dtype,
                "id": str(model_id),
                "project": project_key,
                "name": meta.name,
                "description": meta.description,
                "size": size,
            },
        )
        analytics.track(
            "Upload Model",
            {
                "name": anonymize(meta.name),
                "description": anonymize(meta.description),
                "projectKey": anonymize(project_key),
                "languageVersion": python_version,
                "modelType": meta.model_type.name,
                "threshold": meta.classification_threshold,
                "featureNames": anonymize(meta.feature_names),
                "language": "PYTHON",
                "classificationLabels": anonymize(meta.classification_labels),
                "classificationLabelsDtype": class_label_dtype,
                "loader_module": meta.loader_module,
                "loader_class": meta.loader_class,
                "size": size,
            },
        )

        print(f"Model successfully uploaded to project key '{project_key}' with ID = {model_id}")

    def log_artifacts(self, local_dir, artifact_path=None):
        local_dir = os.path.abspath(local_dir)
        for root, _, filenames in os.walk(local_dir):
            if root == local_dir:
                artifact_dir = artifact_path
            else:
                rel_path = os.path.relpath(root, local_dir)
                rel_path = relative_path_to_artifact_path(rel_path)
                artifact_dir = posixpath.join(artifact_path, rel_path) if artifact_path else rel_path
            for f in filenames:
                self.log_artifact(os.path.join(root, f), artifact_dir)

    def load_artifact(self, local_file: Path, artifact_path: str = None):
        if local_file.exists():
            logger.info(f"Artifact {artifact_path} already exists, skipping download")
            return

        files = self._session.get("artifact-info/" + artifact_path)
        augmented_raise_for_status(files)

        for f in files.json():
            destination_file = local_file / f
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

    def save_dataset_meta(
        self,
        project_key,
        dataset_id,
        meta: DatasetMeta,
        original_size_bytes,
        compressed_size_bytes,
    ):
        self._session.post(
            f"project/{project_key}/datasets",
            json={
                "project": project_key,
                "id": dataset_id,
                "name": meta.name,
                "target": meta.target,
                "columnTypes": meta.column_types,
                "columnDtypes": meta.column_dtypes,
                "originalSizeBytes": original_size_bytes,
                "compressedSizeBytes": compressed_size_bytes,
                "numberOfRows": meta.number_of_rows,
                "categoryFeatures": meta.category_features,
            },
        )
        analytics.track(
            "Upload Dataset",
            {
                "project": anonymize(project_key),
                "id": anonymize(dataset_id),
                "name": anonymize(meta.name),
                "target": anonymize(meta.target),
                "columnTypes": anonymize(meta.column_types),
                "columnDtypes": anonymize(meta.column_dtypes),
                "original_size_bytes": original_size_bytes,
                "compressed_size_bytes": compressed_size_bytes,
            },
        )

        print(f"Dataset successfully uploaded to project key '{project_key}' with ID = {dataset_id}")

    def save_meta(self, endpoint: str, meta: SMT) -> SMT:
        json = self._session.put(endpoint, json=meta.to_json()).json()
        return meta if json is None or "uuid" not in json else meta.from_json(json)

    def load_meta(self, endpoint: str, meta_class: SMT) -> TestFunctionMeta:
        return meta_class.from_json(self._session.get(endpoint).json())

    def get_server_info(self) -> ServerInfo:
        return ServerInfo.parse_obj(self._session.get("/public-api/ml-worker-connect").json())

    def save_test_suite(self, dto: TestSuiteDTO):
        return self._session.post(f"testing/project/{dto.project_key}/suites", json=dto.dict()).json()
