"""API Client to interact with the Giskard app"""

from typing import List

import json
import logging
import os
import posixpath
import sys
import uuid
from pathlib import Path
from urllib.parse import urljoin
from uuid import UUID

import importlib_metadata
from requests import Response
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests_toolbelt import sessions

import giskard
from giskard.client.dtos import (
    DatasetMetaInfo,
    ModelMetaInfo,
    SaveSuiteExecutionDTO,
    ServerInfo,
    SuiteInfo,
    TestSuiteDTO,
)
from giskard.client.io_utils import GiskardJSONSerializer
from giskard.client.project import Project
from giskard.client.python_utils import EXCLUDED_PYLIBS, format_pylib_extras, warning
from giskard.core.core import SMT, DatasetMeta, ModelMeta, TestFunctionMeta
from giskard.utils.analytics_collector import analytics, anonymize
from giskard.utils.environment_detector import COLAB, EnvironmentDetector

UNKNOWN_ERROR = "No details or messages available."

logger = logging.getLogger(__name__)


class GiskardError(Exception):
    def __init__(self, message: str, status: int, code: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def explain_error(resp):
    status = _get_status(resp)

    message = "Unknown error"
    code = f"error.http.{status}"

    if status == 401:
        message = "Not authorized to access this resource. Please check your API key."
    elif status == 403:
        message = "Access denied. Please check your permissions."
    else:
        try:
            message = extract_error_message_from_json(resp)
            message = message or extract_error_message_from_response(resp)
        except Exception as e:
            logger.warning(f"Failed to extract error message from response: {e}")
        message = message or UNKNOWN_ERROR

    return GiskardError(status=status, code=code, message=message)


def extract_error_message_from_response(resp):
    message = ""
    try:
        if resp.title:
            message = resp.title
        if resp.detail:
            message += f" {resp.detail}\n"
        return message
    except Exception:  # noqa
        return message


def extract_error_message_from_json(resp):
    message = ""
    try:
        resp = resp.json()
        if "title" in resp:
            message = f"{resp['title']}:"
        if "detail" in resp:
            message += f" {resp['detail']}\n"
        return message
    except Exception:  # noqa
        return message


def _get_status(resp):
    if isinstance(resp, Response):
        status = resp.status_code
    else:
        status = resp.status

    return status


class ErrorHandlingAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        super(ErrorHandlingAdapter, self).__init__(*args, **kwargs)

    def build_response(self, req, resp):
        resp = super(ErrorHandlingAdapter, self).build_response(req, resp)
        if _get_status(resp) >= 400:
            raise explain_error(resp)

        return resp


class BearerAuth(AuthBase):
    """Defines bearer authentication token as Authorization header"""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


def _limit_str_size(json, field, limit=255):
    if field not in json or not isinstance(json[field], str):
        return

    original_len = len(json[field])
    json[field] = json[field][:limit].encode("utf-16-le")[: limit * 2].decode("utf-16-le", "ignore")

    # Java, js, h2 and postgres use UTF-16 surrogate pairs to calculate str length while python count characters
    if original_len > len(json[field]):
        logger.warning(f"Field '{field} exceeded the limit of {limit} characters and has been truncated")


class GiskardClient:
    def __init__(self, url: str, key: str, hf_token: str = None, verify_ssl: bool = True):
        self.host_url = url
        self.key = key
        self.hf_token = hf_token
        base_url = urljoin(url, "/api/v2/")

        self._session = sessions.BaseUrlSession(base_url=base_url)
        self._session.verify = verify_ssl

        adapter = ErrorHandlingAdapter()

        self._session.mount(url, adapter)

        self._session.auth = BearerAuth(key)

        self._environment = EnvironmentDetector().detect()

        if hf_token:
            self._session.cookies["spaces-jwt"] = hf_token

        server_settings: ServerInfo = self.get_server_info()

        if server_settings.serverVersion != giskard.__version__:
            warning(
                f"Your giskard client version ({giskard.__version__}) does not match the hub version "
                f"({server_settings.serverVersion}). "
                f"Please upgrade your client to the latest version. "
                f'pip install "giskard[hub]>=2.0.0b" -U'
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

    def initialize_kernel(
        self,
        project_key: str,
        exact_deps: bool = False,
        excludes: List[str] = EXCLUDED_PYLIBS,
        only_giskard: bool = False,
    ):
        python_version = f"{sys.version_info[0]}.{sys.version_info[1]}"
        kernel_name = f"{project_key}_kernel"

        analytics.track(
            "Init kernel from env",
            {
                "project_key": anonymize(project_key),
                "kernel_name": anonymize(kernel_name),
                "python_version": python_version,
            },
        )

        kernels = self._session.get("kernels").json()
        frozen_dependencies = [
            f"{dist.name}{format_pylib_extras(dist.name) if exact_deps or dist.name == 'giskard' else ''}=={dist.version}"
            for dist in importlib_metadata.distributions()
            if dist.name not in excludes and (not only_giskard or dist.name == "giskard")
        ]

        existing_kernel = next((kernel for kernel in kernels if kernel["name"] == kernel_name), None)

        if (
            existing_kernel
            and existing_kernel["pythonVersion"] == python_version
            and set(frozen_dependencies).issubset(set(existing_kernel["frozenDependencies"].split("\n")))
        ):
            # A similar kernel already exists
            return existing_kernel["name"]
        elif existing_kernel:
            # A different kernel exists that uses the same name
            kernel_name = f"{kernel_name}_{uuid.uuid4()}"

        self.create_kernel(kernel_name, python_version, frozen_dependencies="\n".join(frozen_dependencies))

        return kernel_name

    def create_kernel(
        self, kernel_name: str, python_version: str, requested_dependencies: str = "", frozen_dependencies: str = ""
    ):
        analytics.track(
            "Create kernel",
            {
                "kernel_name": anonymize(kernel_name),
                "python_version": python_version,
                "requestedDependencies": requested_dependencies,
            },
        )

        self._session.post(
            "kernels",
            json={
                "name": kernel_name,
                "pythonVersion": python_version,
                "requestedDependencies": requested_dependencies,
                "frozenDependencies": frozen_dependencies,
                "type": "PROCESS",
                "version": 0,
            },
        )

    def start_managed_worker(self, kernel_name: str):
        analytics.track("Start worker", {"kernel_name": anonymize(kernel_name)})
        self._session.post(f"kernels/start/{kernel_name}")
        logger.info("The worker is starting up")

    def stop_managed_worker(self, kernel_name: str):
        analytics.track("Stop worker", {"kernel_name": anonymize(kernel_name)})
        self._session.post(f"kernels/stop/{kernel_name}")
        logger.info("The worker has been requested to stop")

    def create_project(self, project_key: str, name: str, description: str = None, kernel_name: str = None) -> Project:
        """Function to create a project in Giskard

        Parameters
        ----------
        project_key : str
            The unique value of the project which will be used to identify  and fetch the project in future
        name : str
            The name of the project
        description : str, optional
            Describe your project, by default None
        kernel_name : str
            The name of the kernel to run on

        Returns
        -------
        Project
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

        if kernel_name is None:
            is_colab = COLAB in self._environment
            kernel_name = self.initialize_kernel(project_key, only_giskard=is_colab)
            if is_colab:
                print(
                    f"Kernel '{kernel_name}' is created on your Giskard hub."
                    "We are initializing the environment with only giskard, since you are in Colab."
                    "Please edit the dependencies in the kernel to align with your environment for model execution."
                )

        try:
            # TODO(Bazire) : use typed object for validation here
            response = self._session.post(
                "project",
                json={"description": description, "key": project_key, "name": name, "kernelName": kernel_name},
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
        analytics.track(
            "hub:dataset:download",
            {
                "project": anonymize(project_key),
                "name": anonymize(info.name),
                "target": anonymize(info.target),
                "columnTypes": anonymize(info.columnTypes),
                "columnDtypes": anonymize(info.columnDtypes),
                "nb_rows": info.numberOfRows,
            },
        )
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
        from mlflow.utils.file_utils import relative_path_to_artifact_path

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
        from mlflow.utils.rest_utils import augmented_raise_for_status

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
        from mlflow.store.artifact.artifact_repo import verify_artifact_path
        from mlflow.utils.rest_utils import augmented_raise_for_status

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
        meta_json = meta.to_json()

        _limit_str_size(meta_json, "name")
        _limit_str_size(meta_json, "display_name")

        data = json.dumps(meta_json, cls=GiskardJSONSerializer)

        response_json = self._session.put(endpoint, data=data, headers={"Content-Type": "application/json"}).json()
        return meta if response_json is None or "uuid" not in response_json else meta.from_json(response_json)

    def load_meta(self, endpoint: str, meta_class: SMT) -> TestFunctionMeta:
        return meta_class.from_json(self._session.get(endpoint).json())

    def get_server_info(self) -> ServerInfo:
        resp = self._session.get("/public-api/ml-worker-connect")
        try:
            return ServerInfo.parse_obj(resp.json())
        except Exception:
            raise explain_error(resp)

    def save_test_suite(self, dto: TestSuiteDTO):
        return self._session.post(f"testing/project/{dto.project_key}/suites", json=dto.dict()).json()

    def update_test_suite(self, suite_id: int, dto: TestSuiteDTO):
        return self._session.put(f"testing/project/{dto.project_key}/suite/{suite_id}", json=dto.dict()).json()

    def save_test_suite_execution_result(self, project_key: str, dto: SaveSuiteExecutionDTO):
        return self._session.post(f"testing/project/{project_key}/executions", json=dto.dict()).json()
