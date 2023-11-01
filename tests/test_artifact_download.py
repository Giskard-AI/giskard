
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
    MockedClient,
    MockedProjectCacheDir,
    fixup_mocked_artifact_meta_version,
    get_local_cache_callable_artifact,
    register_uri_for_artifact_meta_info,
    register_uri_for_artifact_info,
    get_url_for_artifact_meta_info,
    get_url_for_artifacts_base,
    local_save_artifact_under_giskard_home_cache,
    is_url_requested,
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


def test_download_global_test_function_from_registry():
    cf: Artifact = my_custom_test

    # Load from registry using uuid without client
    download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=None, project_key=None)

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
def test_download_global_test_function_from_local(cf):
    project_key = str(uuid.uuid4())
    with MockedProjectCacheDir(project_key):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID to ensure not loading from registry

        local_save_artifact_under_giskard_home_cache(cf, project_key=None)

        # Load from registry using uuid without client
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=None, project_key=None)

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
def test_download_callable_function(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID to ensure not loading from registry
        cache_dir = get_local_cache_callable_artifact(project_key=None, artifact=cf)

        # Save to temp
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            cf.save(tmpdir_path)
            # Check saved file
            assert (tmpdir_path / CALLABLE_FUNCTION_PKL_CACHE).exists()
            assert (tmpdir_path / CALLABLE_FUNCTION_META_CACHE).exists()

            requested_urls = []
            # Fixup the differences from Backend
            meta_info = fixup_mocked_artifact_meta_version(cf.meta.to_json())
            # Fixup the name to avoid load from module
            meta_info.update({
                "name": f"fake_{cf._get_name()}",
            })
            url = get_url_for_artifact_meta_info(cf, project_key=None)
            mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
            requested_urls.append(url)

            # Register for Artifact info
            requested_urls.extend(register_uri_for_artifact_info(mr, cf, project_key=None))

            # Register for Artifacts content
            artifacts_base_url = get_url_for_artifacts_base(cf, project_key=None)
            for file in [CALLABLE_FUNCTION_META_CACHE, CALLABLE_FUNCTION_PKL_CACHE]:
                with open(tmpdir_path / file, "rb") as f:
                    mr.register_uri(
                        method=requests_mock.GET,
                        url=posixpath.join(artifacts_base_url, file),
                        content=f.read(),
                    )
                    requested_urls.append(posixpath.join(artifacts_base_url, file))

            # Download: should not call load_artifact to request and download
            download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=None)

            for requested_url in requested_urls:
                assert is_url_requested(mr.request_history, requested_url)

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
def test_download_global_callable_function_from_module(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID to ensure not loading from registry
        cache_dir = get_local_cache_callable_artifact(project_key=None, artifact=cf)

        requested_urls = []
        # Prepare global URL
        requested_urls.extend(register_uri_for_artifact_meta_info(mr, cf, project_key=None))

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=None)

        for requested_url in requested_urls:
            assert is_url_requested(mr.request_history, requested_url)

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
def test_download_global_callable_function_from_cache(cf: Artifact):
    with MockedClient(mock_all=False) as (client, mr):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID
        cache_dir = get_local_cache_callable_artifact(project_key=None, artifact=cf)

        # Save to local cache
        local_save_artifact_under_giskard_home_cache(artifact=cf, project_key=None)
        assert (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
        assert (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()

        requested_urls = register_uri_for_artifact_meta_info(mr, cf, project_key=None)

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=None)

        for requested_url in requested_urls:
            assert is_url_requested(mr.request_history, requested_url)

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
    project_key = str(uuid.uuid4())
    with MockedClient(mock_all=False) as (client, mr), MockedProjectCacheDir(project_key=project_key):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID to ensure not loading from registry
        cache_dir = get_local_cache_callable_artifact(project_key=project_key, artifact=cf)

        # Save to temp
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            cf.save(tmpdir_path)
            # Check saved file
            assert (tmpdir_path / CALLABLE_FUNCTION_PKL_CACHE).exists()
            assert (tmpdir_path / CALLABLE_FUNCTION_META_CACHE).exists()

            requested_urls = []
            # Fixup the differences from Backend
            meta_info = fixup_mocked_artifact_meta_version(cf.meta.to_json())
            # Fixup the name to avoid load from module
            meta_info.update({
                "name": f"fake_{cf._get_name()}",
            })
            url = get_url_for_artifact_meta_info(cf, project_key=project_key)
            mr.register_uri(method=requests_mock.GET, url=url, json=meta_info)
            requested_urls.append(url)

            # Register for Artifact info
            requested_urls.extend(register_uri_for_artifact_info(mr, cf, project_key=project_key))

            # Register for Artifacts content
            artifacts_base_url = get_url_for_artifacts_base(cf, project_key=project_key)
            for file in [CALLABLE_FUNCTION_META_CACHE, CALLABLE_FUNCTION_PKL_CACHE]:
                with open(tmpdir_path / file, "rb") as f:
                    mr.register_uri(
                        method=requests_mock.GET,
                        url=posixpath.join(artifacts_base_url, file),
                        content=f.read(),
                    )
                    requested_urls.append(posixpath.join(artifacts_base_url, file))

            # Download: should not call load_artifact to request and download
            download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=project_key)

            for requested_url in requested_urls:
                assert is_url_requested(mr.request_history, requested_url)

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
    project_key = str(uuid.uuid4())
    with MockedClient(mock_all=False) as (client, mr), MockedProjectCacheDir(project_key):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID to ensure not loading from registry
        cache_dir = get_local_cache_callable_artifact(project_key=project_key, artifact=cf)

        requested_urls = []
        # Prepare global URL
        requested_urls.extend(register_uri_for_artifact_meta_info(mr, cf, project_key))

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=project_key)

        for requested_url in requested_urls:
            assert is_url_requested(mr.request_history, requested_url)

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
    project_key = str(uuid.uuid4())
    with MockedClient(mock_all=False) as (client, mr), MockedProjectCacheDir(project_key):
        cf.meta.uuid = str(uuid.uuid4())    # Regenerate a UUID to ensure not loading from registry
        cache_dir = get_local_cache_callable_artifact(project_key=project_key, artifact=cf)

        # Save to local cache
        local_save_artifact_under_giskard_home_cache(artifact=cf, project_key=project_key)
        assert (cache_dir / CALLABLE_FUNCTION_PKL_CACHE).exists()
        assert (cache_dir / CALLABLE_FUNCTION_META_CACHE).exists()

        requested_urls = register_uri_for_artifact_meta_info(mr, cf, project_key)

        # Download: should not call load_artifact to request and download
        download_cf = cf.__class__.download(uuid=cf.meta.uuid, client=client, project_key=project_key)

        for requested_url in requested_urls:
            assert is_url_requested(mr.request_history, requested_url)

        # Check the downloaded info
        assert download_cf.__class__ is cf.__class__
        assert download_cf.meta.uuid == cf.meta.uuid
