import uuid
import pytest

from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.testing.test_result import TestResult as GiskardTestResult
from giskard.ml_worker.websocket import listener
from giskard.testing.tests import debug_prefix
from giskard import test

from tests import utils


@test
def my_simple_test():
    return GiskardTestResult(passed=False)


@pytest.mark.parametrize("debug", [
    False, None
])
def test_websocket_actor_run_ad_hoc_test_no_debug(debug):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test.meta.uuid,
            arguments=[],
            debug=debug,
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test, None)

            reply = listener.run_ad_hoc_test(client=client, params=params)
            assert isinstance(reply, websocket.RunAdHocTest)
            assert reply.results and 1 == len(reply.results)
            assert my_simple_test.meta.uuid == reply.results[0].testUuid
            assert not reply.results[0].result.passed
            assert not reply.results[0].result.is_error


def test_websocket_actor_run_ad_hoc_test_debug_no_return():
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test.meta.uuid,
            arguments=[],
            debug=True,
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test, None)

            with pytest.raises(ValueError, match=r"^This test does not return any examples to debug.*"):
                listener.run_ad_hoc_test(client=client, params=params)


@test
def my_simple_test_debug_incorrect_impl(dataset: Dataset, debug: bool = False):
    # The debug param should not be ignored,
    # otherwise raising ValueError due to missing debug_info when not debugging
    output_ds = dataset.copy()
    output_ds.name = debug_prefix + "my_simple_test_debug_incorrect_impl"
    return GiskardTestResult(passed=False, output_df=output_ds)


def test_websocket_actor_run_ad_hoc_test_debug_incorrect_impl(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_debug_incorrect_impl.meta.uuid,
            arguments=[
                websocket.FuncArgument(
                    name="dataset",
                    none=False,
                    dataset=websocket.ArtifactRef(
                        project_key=project_key,
                        id=str(enron_data.id),
                    ),
                ),
            ],
            debug=False,
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_debug_incorrect_impl, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)

            with pytest.raises(ValueError, match=r".*extract_debug_info did not return the information needed.*"):
                listener.run_ad_hoc_test(client=client, params=params)


@test
def my_simple_test_debug(dataset: Dataset, debug: bool = False):
    output_ds = None
    if debug:
        output_ds = dataset.copy()
        output_ds.name = debug_prefix + "my_simple_test_debug"
    return GiskardTestResult(passed=False, output_df=output_ds)


def test_websocket_actor_run_ad_hoc_test_debug(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_debug.meta.uuid,
            arguments=[
                websocket.FuncArgument(
                    name="dataset",
                    none=False,
                    dataset=websocket.ArtifactRef(
                        project_key=project_key,
                        id=str(enron_data.id),
                    ),
                ),
            ],
            debug=True,
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_debug, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)
            utils.register_uri_for_any_dataset_artifact_info_upload(mr, register_files=True)

            reply = listener.run_ad_hoc_test(client=client, params=params)
            assert isinstance(reply, websocket.RunAdHocTest)
            assert reply.results and 1 == len(reply.results)
            assert my_simple_test_debug.meta.uuid == reply.results[0].testUuid
            assert not reply.results[0].result.passed
            assert not reply.results[0].result.is_error
            assert not reply.results[0].result.output_df
            assert reply.results[0].result.output_df_id


@test
def my_simple_test_debug_no_name(dataset: Dataset, debug: bool = False):
    output_ds = None
    if debug:
        output_ds = dataset.copy()
        output_ds.name = None
    return GiskardTestResult(passed=False, output_df=output_ds)


def test_websocket_actor_run_ad_hoc_test_debug_no_name(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_debug_no_name.meta.uuid,
            arguments=[
                websocket.FuncArgument(
                    name="dataset",
                    none=False,
                    dataset=websocket.ArtifactRef(
                        project_key=project_key,
                        id=str(enron_data.id),
                    ),
                ),
            ],
            debug=True,
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_debug_no_name, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)

            with pytest.raises(TypeError, match=".*NoneType.*"):
                listener.run_ad_hoc_test(client=client, params=params)

