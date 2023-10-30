
import posixpath
import uuid
import pandas as pd

import tempfile
from pathlib import Path

import pytest
import requests_mock

from giskard import slicing_function, transformation_function
from giskard.ml_worker.core.savable import Artifact
from giskard.ml_worker.testing.test_result import TestResult as GiskardTestResult
from giskard import test

from tests.utils import (
    CALLABLE_FUNCTION_META_CACHE,
    CALLABLE_FUNCTION_PKL_CACHE,
    get_local_cache_callable_artifact,
    MockedClient,
    local_save_artifact_under_giskard_home_cache,
    fixup_mocked_artifact_meta_version,
)


BASE_CLIENT_URL = "http://giskard-host:12345/api/v2"


# Define a test function
@test
def my_custom_test(model, data):
    return GiskardTestResult(passed=True)


# Define a slicing function
@slicing_function(row_level=False)
def head_slice(df: pd.DataFrame) -> pd.DataFrame:
    return df.head(10)


# Define a transformation function
@transformation_function()
def do_nothing(row):
    return row


@pytest.mark.parametrize(
    "cf",
    [
        my_custom_test, # Test
        head_slice,     # Slice
        do_nothing,     # Transformation
    ],
)
def test_download_callable_function(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=None, artifact=cf)

        # Save to temp
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            cf.save(tmpdir_path)
            # Check saved file
            assert (tmpdir_path / CALLABLE_FUNCTION_PKL_CACHE).exists()
            assert (tmpdir_path / CALLABLE_FUNCTION_META_CACHE).exists()

            # Prepare global URL
            url = posixpath.join(BASE_CLIENT_URL, cf._get_name(), cf.meta.uuid)
            artifact_info_url = posixpath.join(BASE_CLIENT_URL, "artifact-info", "global", cf._get_name(), cf.meta.uuid)
            artifacts = [
                CALLABLE_FUNCTION_PKL_CACHE, CALLABLE_FUNCTION_META_CACHE,
            ]
            artifacts_base_url = posixpath.join(BASE_CLIENT_URL, "artifacts", "global", cf._get_name(), cf.meta.uuid)
            meta_info = cf.meta.to_json()
            # Fixup the name to avoid load from module
            meta_info.update({
                "name": f"fake_{cf._get_name()}",
            })
            # Fixup the differences from Backend
            meta_info = fixup_mocked_artifact_meta_version(meta_info)

            mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
            mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)
            mr.register_uri(
                method=requests_mock.GET,
                url=posixpath.join(artifacts_base_url, CALLABLE_FUNCTION_PKL_CACHE),
                body=open(tmpdir_path / CALLABLE_FUNCTION_PKL_CACHE, "rb")
            )
            mr.register_uri(
                method=requests_mock.GET,
                url=posixpath.join(artifacts_base_url, CALLABLE_FUNCTION_META_CACHE),
                body=open(tmpdir_path / CALLABLE_FUNCTION_META_CACHE, "rb")
            )

            # Download: should not call load_artifact to request and download
            download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=None)
            # Check the downloaded info
            assert download_cf.__class__ is cf.__class__
            assert download_cf.meta.uuid == cf.meta.uuid
            # Check the downloaded files
            assert (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
            assert (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()


@pytest.mark.parametrize(
    "cf",
    [
        my_custom_test, # Test
        head_slice,     # Slice
        do_nothing,     # Transformation
    ],
)
def test_download_callable_function_from_module(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=None, artifact=cf)

        # Prepare global URL
        url = posixpath.join(BASE_CLIENT_URL, cf._get_name(), cf.meta.uuid)
        artifact_info_url = posixpath.join(BASE_CLIENT_URL, "artifact-info", "global", cf._get_name(), cf.meta.uuid)
        artifacts = [
            CALLABLE_FUNCTION_PKL_CACHE, CALLABLE_FUNCTION_META_CACHE,
        ]
        meta_info = cf.meta.to_json()
        # Fixup the differences from Backend
        meta_info = fixup_mocked_artifact_meta_version(meta_info)

        mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
        mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=None)
        # Check the downloaded info
        assert download_cf.__class__ is cf.__class__
        assert download_cf.meta.uuid == cf.meta.uuid
        # Check the files that do not need to be downloaded
        assert not (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
        assert not (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()


@pytest.mark.parametrize(
    "cf",
    [
        my_custom_test, # Test
        head_slice,     # Slice
        do_nothing,     # Transformation
    ],
)
def test_download_callable_function_from_cache(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=None, artifact=cf)

        # Save to local cache
        local_save_artifact_under_giskard_home_cache(artifact=cf, project_key=None)
        assert (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
        assert (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()

        # Prepare global URL
        url = posixpath.join(BASE_CLIENT_URL, cf._get_name(), cf.meta.uuid)
        artifact_info_url = posixpath.join(BASE_CLIENT_URL, "artifact-info", "global", cf._get_name(), cf.meta.uuid)
        artifacts = [
            CALLABLE_FUNCTION_PKL_CACHE, CALLABLE_FUNCTION_META_CACHE,
        ]
        meta_info = cf.meta.to_json()
        # Fixup the differences from Backend
        meta_info = fixup_mocked_artifact_meta_version(meta_info)

        mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
        mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=None)
        # Check the downloaded info
        assert download_cf.__class__ is cf.__class__
        assert download_cf.meta.uuid == cf.meta.uuid



@pytest.mark.parametrize(
    "cf",
    [
        my_custom_test, # Test
        head_slice,     # Slice
        do_nothing,     # Transformation
    ],
)
def test_download_callable_function_in_project(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        project_key = str(uuid.uuid4())
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=project_key, artifact=cf)

        # Save to temp
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            cf.save(tmpdir_path)
            # Check saved file
            assert (tmpdir_path / CALLABLE_FUNCTION_PKL_CACHE).exists()
            assert (tmpdir_path / CALLABLE_FUNCTION_META_CACHE).exists()

            # Prepare global URL
            url = posixpath.join(BASE_CLIENT_URL, "project", project_key, cf._get_name(), cf.meta.uuid)
            artifact_info_url = posixpath.join(BASE_CLIENT_URL, "artifact-info", project_key, cf._get_name(), cf.meta.uuid)
            artifacts = [
                CALLABLE_FUNCTION_PKL_CACHE, CALLABLE_FUNCTION_META_CACHE,
            ]
            artifacts_base_url = posixpath.join(BASE_CLIENT_URL, "artifacts", project_key, cf._get_name(), cf.meta.uuid)
            meta_info = cf.meta.to_json()
            # Fixup the name to avoid load from module
            meta_info.update({
                "name": f"fake_{cf._get_name()}",
            })
            # Fixup the differences from Backend
            meta_info = fixup_mocked_artifact_meta_version(meta_info)

            mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
            mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)
            mr.register_uri(
                method=requests_mock.GET,
                url=posixpath.join(artifacts_base_url, CALLABLE_FUNCTION_PKL_CACHE),
                body=open(tmpdir_path / CALLABLE_FUNCTION_PKL_CACHE, "rb")
            )
            mr.register_uri(
                method=requests_mock.GET,
                url=posixpath.join(artifacts_base_url, CALLABLE_FUNCTION_META_CACHE),
                body=open(tmpdir_path / CALLABLE_FUNCTION_META_CACHE, "rb")
            )

            # Download: should not call load_artifact to request and download
            download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=project_key)
            # Check the downloaded info
            assert download_cf.__class__ is cf.__class__
            assert download_cf.meta.uuid == cf.meta.uuid
            # Check the downloaded files
            assert (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
            assert (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()


@pytest.mark.parametrize(
    "cf",
    [
        my_custom_test, # Test
        head_slice,     # Slice
        do_nothing,     # Transformation
    ],
)
def test_download_callable_function_from_module_in_project(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        project_key = str(uuid.uuid4())
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=project_key, artifact=cf)

        # Prepare global URL
        url = posixpath.join(BASE_CLIENT_URL, "project", project_key, cf._get_name(), cf.meta.uuid)
        artifact_info_url = posixpath.join(BASE_CLIENT_URL, "artifact-info", "project", project_key, cf.meta.uuid)
        artifacts = [
            CALLABLE_FUNCTION_PKL_CACHE, CALLABLE_FUNCTION_META_CACHE,
        ]
        meta_info = cf.meta.to_json()
        # Fixup the differences from Backend
        meta_info = fixup_mocked_artifact_meta_version(meta_info)

        mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
        mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=project_key)
        # Check the downloaded info
        assert download_cf.__class__ is cf.__class__
        assert download_cf.meta.uuid == cf.meta.uuid
        # Check the files that do not need to be downloaded
        assert not (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
        assert not (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()


@pytest.mark.parametrize(
    "cf",
    [
        my_custom_test, # Test
        head_slice,     # Slice
        do_nothing,     # Transformation
    ],
)
def test_download_callable_function_from_cache_in_project(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        project_key = str(uuid.uuid4())
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=project_key, artifact=cf)

        # Save to local cache
        local_save_artifact_under_giskard_home_cache(artifact=cf, project_key=project_key)
        assert (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
        assert (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()

        # Prepare global URL
        url = posixpath.join(BASE_CLIENT_URL, "project", project_key, cf._get_name(), cf.meta.uuid)
        artifact_info_url = posixpath.join(BASE_CLIENT_URL, "artifact-info", "project", project_key, cf._get_name(), cf.meta.uuid)
        artifacts = [
            CALLABLE_FUNCTION_PKL_CACHE, CALLABLE_FUNCTION_META_CACHE,
        ]
        meta_info = cf.meta.to_json()
        # Fixup the differences from Backend
        meta_info = fixup_mocked_artifact_meta_version(meta_info)

        mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
        mr.register_uri(method=requests_mock.GET, url=artifact_info_url, json=artifacts)

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=project_key)
        # Check the downloaded info
        assert download_cf.__class__ is cf.__class__
        assert download_cf.meta.uuid == cf.meta.uuid
