from typing import Optional

import glob
import logging
import os
import platform
import posixpath
import re
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import requests
import requests_mock

from giskard.client import dtos
from giskard.core.savable import Artifact
from giskard.datasets.base import Dataset
from giskard.llm.embeddings.base import BaseEmbedding
from giskard.models.base.model import BaseModel
from giskard.path_utils import get_size
from giskard.settings import settings
from giskard.utils.file_utils import get_file_name

logger = logging.getLogger(__name__)
resource_dir: Path = Path.home() / ".giskard"

headers_to_match = {"Authorization": "Bearer SECRET_TOKEN", "Content-Type": "application/json"}

CALLABLE_FUNCTION_PKL_CACHE = "data.pkl"
CALLABLE_FUNCTION_META_CACHE = "meta.yaml"

CLIENT_BASE_URL = "http://giskard-host:12345/api/v2"

TEST_UUID = "00000000-0000-0000-0000-000000000000"


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


def is_url_requested(last_requests, url):
    for i in last_requests:
        if i.url == url:
            return True
    return False


def get_email_files():
    out_path = Path.home() / ".giskard"
    enron_path = out_path / "enron_with_categories"
    if not enron_path.exists():
        url = "https://bailando.berkeley.edu/enron/enron_with_categories.tar.gz"
        logger.info(f"Downloading test data from: {url}")
        response = requests.get(url, stream=True)
        file = tarfile.open(fileobj=response.raw, mode="r|gz")
        os.makedirs(out_path, exist_ok=True)
        file.extractall(path=out_path)
    return [f.replace(".cats", "") for f in glob.glob(str(enron_path) + "/*/*.cats")]


class MockedProjectCacheDir:
    def __init__(self):
        self.initial_cache = settings.cache_dir
        self.mocked_cache = tempfile.TemporaryDirectory(suffix="cache", dir=settings.home_dir)
        settings.cache_dir = self.mocked_cache.name

    def __enter__(self):
        return self.mocked_cache.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mocked_cache.__exit__(exc_type, exc_val, exc_tb)
        settings.cache_dir = self.initial_cache


def get_local_cache_base():
    return settings.home_dir / settings.cache_dir


def get_local_cache_artifact(name: str, uuid: str):
    return get_local_cache_base() / name / uuid


def get_local_cache_callable_artifact(artifact: Artifact):
    return get_local_cache_artifact(artifact._get_name(), artifact.meta.uuid)


def local_save_model_under_giskard_home_cache(model: BaseModel):
    local_path_model = get_local_cache_artifact("models", str(model.id))
    local_path_model.mkdir(parents=True)
    model.save(local_path=local_path_model)


def local_save_dataset_under_giskard_home_cache(dataset: Dataset):
    local_path_dataset = get_local_cache_artifact("datasets", str(dataset.id))
    local_path_dataset.mkdir(parents=True)
    dataset.save(local_path=local_path_dataset, dataset_id=dataset.id)


def local_save_artifact_under_giskard_home_cache(artifact: Artifact):
    local_path = get_local_cache_callable_artifact(artifact)
    local_path.mkdir(parents=True)
    artifact.save(local_dir=local_path)


def fixup_mocked_artifact_meta_version(meta_info):
    meta_info.update(
        {
            "displayName": meta_info.pop("display_name"),
            "moduleDoc": meta_info.pop("module_doc"),
            "version": 1,
        }
    )
    for arg in meta_info["args"] if meta_info["args"] else []:
        arg.update({"defaultValue": arg.pop("default")})
    return meta_info


def mock_dataset_meta_info(dataset: Dataset, project_key: str):
    meta = dataset.meta
    with tempfile.TemporaryDirectory() as tmpdir:
        original_size_bytes, compressed_size_bytes = dataset.save(Path(tmpdir), str(dataset.id))

    logger.debug(f"The project_key {project_key} will be ignored by Backend")

    dataset_meta_info = dtos.DatasetMetaInfo(
        target=meta.target,
        columnTypes=meta.column_types,
        columnDtypes=meta.column_dtypes,
        numberOfRows=meta.number_of_rows,
        categoryFeatures=meta.category_features,
        name=meta.name,
        originalSizeBytes=original_size_bytes,
        compressedSizeBytes=compressed_size_bytes,
        createdDate="now",  # createdDate is not nullable but not used
        id=str(dataset.id),
    )
    return dataset_meta_info.dict()


def mock_model_meta_info(model: BaseModel, project_key: str):
    meta = model.meta
    size = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        model.save(tmpdir)
        size = get_size(tmpdir)

    logger.debug(f"The project_key {project_key} will be ignored by Backend")

    model_meta_info = dtos.ModelMetaInfo(
        id=str(model.id),
        name=meta.name or model.__class__.__name__,
        modelType=meta.model_type.name.upper(),
        featureNames=meta.feature_names,
        threshold=meta.classification_threshold,
        description=meta.description,
        classificationLabels=meta.classification_labels,
        classificationLabelsDtype=(
            None
            if (not meta.classification_labels or not len(meta.classification_labels))
            else type(meta.classification_labels[0]).__name__
        ),
        languageVersion=platform.python_version(),
        language="PYTHON",
        size=size,
        createdDate="now",  # The field createdDate is not nullable but not used
        projectId=0,  # Mock a project ID
    )
    return model_meta_info.dict()


def get_url_for_artifact_meta_info(cf: Artifact, project_key: str):
    return posixpath.join(CLIENT_BASE_URL, "project", project_key, cf._get_name(), cf.meta.uuid)


def get_url_for_artifacts_base(cf: Artifact):
    return posixpath.join(CLIENT_BASE_URL, "artifacts", cf._get_name(), cf.meta.uuid)


def get_url_for_dataset(dataset: Dataset, project_key: str):
    return posixpath.join(CLIENT_BASE_URL, "project", project_key, "datasets", str(dataset.id))


def get_url_for_model(model: BaseModel, project_key: str):
    return posixpath.join(CLIENT_BASE_URL, "project", project_key, "models", str(model.id))


def register_uri_for_artifact_meta_info(mr: requests_mock.Mocker, cf: Artifact, project_key: str):
    url = get_url_for_artifact_meta_info(cf, project_key)
    # Fixup the differences from Backend
    meta_info = fixup_mocked_artifact_meta_version(cf.meta.to_json())

    mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
    return [url]


def register_uri_for_artifact_info(mr: requests_mock.Mocker, cf: Artifact, project_key: Optional[str] = None):
    artifact_info_url = (
        posixpath.join(CLIENT_BASE_URL, "artifact-info", cf._get_name(), cf.meta.uuid)
        if project_key
        else posixpath.join(CLIENT_BASE_URL, "artifact-info", cf._get_name(), cf.meta.uuid)
    )
    artifacts = [
        CALLABLE_FUNCTION_PKL_CACHE,
        CALLABLE_FUNCTION_META_CACHE,
    ]
    mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)
    return [artifact_info_url]


def register_uri_for_artifacts_under_dir(
    mr: requests_mock.Mocker, dir_path: Path, artifacts_base_url, register_file_contents: bool = False
):
    artifacts = []
    artifact_urls = []
    for f in dir_path.iterdir():
        artifacts.append(f.name)
        if register_file_contents:
            with f.open("rb") as content:
                # Read the entire file can use a lot of memory
                mr.register_uri(
                    method=requests_mock.GET, url=posixpath.join(artifacts_base_url, f.name), content=content.read()
                )
                artifact_urls.append(posixpath.join(artifacts_base_url, f.name))
    return artifacts, artifact_urls


def register_uri_for_dataset_meta_info(mr: requests_mock.Mocker, dataset: Dataset, project_key: str):
    dataset_url = get_url_for_dataset(dataset, project_key)
    dataset_meta_info = mock_dataset_meta_info(dataset, project_key)
    mr.register_uri(method=requests_mock.GET, url=dataset_url, json=dataset_meta_info)
    return [dataset_url]


def register_uri_for_dataset_artifact_info(
    mr: requests_mock.Mocker, dataset: Dataset, project_key: str, register_file_contents: bool = False
):
    artifact_info_url = posixpath.join(CLIENT_BASE_URL, "artifact-info", "datasets", str(dataset.id))
    artifacts_base_url = posixpath.join(CLIENT_BASE_URL, "artifacts", "datasets", str(dataset.id))
    artifacts = []
    artifact_urls = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        dataset.save(Path(tmpdir), dataset.id)  # Save dataset in temp dir
        artifacts, artifact_urls = register_uri_for_artifacts_under_dir(
            mr, tmpdir_path, artifacts_base_url, register_file_contents
        )

    mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)
    artifact_urls.extend([artifact_info_url])
    return artifact_urls


def register_uri_for_any_tests_artifact_info_upload(mr: requests_mock.Mocker, register_files=False):
    meta_info_pattern = re.compile("http://giskard-host:12345/api/v2/project/.*/tests")
    artifacts_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/tests/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    mr.register_uri(method=requests_mock.PUT, url=meta_info_pattern, json={})
    if register_files:
        mr.register_uri(method=requests_mock.POST, url=artifacts_url_pattern)


def register_uri_for_any_slices_artifact_info_upload(mr: requests_mock.Mocker, register_files=False):
    meta_info_pattern = re.compile("http://giskard-host:12345/api/v2/project/.*/slices")
    artifacts_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/slices/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    mr.register_uri(method=requests_mock.PUT, url=meta_info_pattern, json={})
    if register_files:
        mr.register_uri(method=requests_mock.POST, url=artifacts_url_pattern)


def register_uri_for_any_transforms_artifact_info_upload(mr: requests_mock.Mocker, register_files=False):
    meta_info_pattern = re.compile("http://giskard-host:12345/api/v2/project/.*/transformations")
    artifacts_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/transformations/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    mr.register_uri(method=requests_mock.PUT, url=meta_info_pattern, json={})
    if register_files:
        mr.register_uri(method=requests_mock.POST, url=artifacts_url_pattern)


def register_uri_for_any_dataset_artifact_info_upload(mr: requests_mock.Mocker, register_files=False):
    meta_info_pattern = re.compile("http://giskard-host:12345/api/v2/project/.*/datasets")
    artifacts_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/datasets/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*"
    )
    mr.register_uri(method=requests_mock.POST, url=meta_info_pattern)
    if register_files:
        mr.register_uri(method=requests_mock.POST, url=artifacts_url_pattern)


def register_uri_for_model_meta_info(mr: requests_mock.Mocker, model: BaseModel, project_key: str):
    model_url = get_url_for_model(model, project_key)
    model_meta_info = mock_model_meta_info(model, project_key=project_key)
    mr.register_uri(method=requests_mock.GET, url=model_url, json=model_meta_info)
    return [model_url]


def register_uri_for_model_artifact_info(
    mr: requests_mock.Mocker, model: BaseModel, project_key: str, register_file_contents: bool = False
):
    artifact_info_url = posixpath.join(CLIENT_BASE_URL, "artifact-info", "models", str(model.id))
    artifacts_base_url = posixpath.join(CLIENT_BASE_URL, "artifacts", "models", str(model.id))
    artifacts = []
    artifact_urls = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        model.save(Path(tmpdir))  # Save dataset in temp dir
        artifacts, artifact_urls = register_uri_for_artifacts_under_dir(
            mr, tmpdir_path, artifacts_base_url, register_file_contents
        )

    mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)
    artifact_urls.extend([artifact_info_url])
    return artifact_urls


def register_uri_for_inspection(mr: requests_mock.Mocker, project_key: str, inspection_id: int, sample: bool):
    url = posixpath.join(CLIENT_BASE_URL, "artifacts", f"models/inspections/{inspection_id}")
    calculated_url = posixpath.join(url, get_file_name("calculated", "csv", sample))
    predictions_url = posixpath.join(url, get_file_name("predictions", "csv", sample))
    mr.register_uri(method=requests_mock.POST, url=calculated_url, json={})
    mr.register_uri(method=requests_mock.POST, url=predictions_url, json={})


class DummyEmbedding(BaseEmbedding):
    def embed(self, texts):
        return np.random.uniform(size=(len(texts), 768))
