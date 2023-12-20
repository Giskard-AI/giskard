import random
import uuid

import pandas as pd
import pytest

import giskard
from giskard import test
from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.testing.test_result import TestResult as GiskardTestResult, TestMessage, TestMessageLevel
from giskard.ml_worker.websocket import listener
from giskard.models.base import BaseModel
from giskard.testing.tests import debug_prefix
from tests import utils


@test
def my_simple_test():
    return GiskardTestResult(passed=False)


@test
def my_simple_test_successful():
    return GiskardTestResult(passed=True)


@test
def my_simple_test__legacy_debug():
    return GiskardTestResult(passed=True, output_df=Dataset(pd.DataFrame({"test": [1]})))


@test
def my_simple_test_error():
    raise ValueError("Actively raise an error in the test.")


@pytest.mark.parametrize("debug", [False, None])
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


@test
def my_simple_test_legacy_debug(dataset: Dataset, debug: bool = False):
    output_ds = None
    if debug:
        output_ds = dataset.copy()
        output_ds.name = debug_prefix + "my_simple_test_debug"
    return GiskardTestResult(passed=False, output_df=output_ds)


@giskard.test()
def same_prediction(left: BaseModel, right: BaseModel, ds: giskard.Dataset):
    left_pred = left.predict(ds)
    right_pred = right.predict(ds)
    return giskard.TestResult(passed=list(left_pred.raw_prediction) == list(right_pred.raw_prediction))


def test_websocket_actor_run_ad_hoc_test_legacy_debug(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_legacy_debug.meta.uuid,
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
            projectKey="projectKey",
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_legacy_debug, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)
            utils.register_uri_for_any_dataset_artifact_info_upload(mr, register_files=True)

            reply = listener.run_ad_hoc_test(client=client, params=params)
            assert isinstance(reply, websocket.RunAdHocTest)
            assert reply.results and 1 == len(reply.results)
            assert my_simple_test_legacy_debug.meta.uuid == reply.results[0].testUuid
            assert not reply.results[0].result.passed
            assert not reply.results[0].result.is_error
            assert reply.results[0].result.failed_indexes


def test_websocket_actor_run_ad_hoc_test_legacy_no_client(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_legacy_debug.meta.uuid,
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

        with pytest.raises(RuntimeError):
            listener.run_ad_hoc_test(client=None, params=params)


def test_websocket_actor_run_ad_hoc_test_legacy_no_project_key(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_legacy_debug.meta.uuid,
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

        with utils.MockedClient(mock_all=False) as (client, mr), pytest.raises(ValueError):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_legacy_debug, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)

            listener.run_ad_hoc_test(client=client, params=params)


@test
def my_simple_test_debug(dataset: Dataset, debug: bool = False):
    return GiskardTestResult(passed=False, output_ds=[dataset.slice(lambda df: df.head(1), row_level=False)])


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
            assert reply.results[0].result.failed_indexes
            assert reply.results[0].result.failed_indexes is not None
            assert 1 == len(reply.results[0].result.failed_indexes)
            assert str(enron_data.id) in reply.results[0].result.failed_indexes
            assert 0 == reply.results[0].result.failed_indexes[str(enron_data.id)][0]


@test
def my_simple_test_debug_multiple_datasets(dataset: Dataset, dataset2: Dataset, debug: bool = False):
    return GiskardTestResult(
        passed=False,
        output_ds=[
            dataset.slice(lambda df: df.head(1), row_level=False),
            dataset2.slice(lambda df: df.head(1), row_level=False),
        ],
    )


def test_websocket_actor_run_ad_hoc_test_debug_multiple_datasets(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        # Create the second dataset
        dataset2 = enron_data.copy()
        dataset2.original_id = uuid.uuid4()
        dataset2.id = dataset2.original_id
        utils.local_save_dataset_under_giskard_home_cache(dataset2, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_debug_multiple_datasets.meta.uuid,
            arguments=[
                websocket.FuncArgument(
                    name="dataset",
                    none=False,
                    dataset=websocket.ArtifactRef(
                        project_key=project_key,
                        id=str(enron_data.id),
                    ),
                ),
                websocket.FuncArgument(
                    name="dataset2",
                    none=False,
                    dataset=websocket.ArtifactRef(
                        project_key=project_key,
                        id=str(dataset2.id),
                    ),
                ),
            ],
            debug=True,
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_debug_multiple_datasets, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)
            utils.register_uri_for_dataset_meta_info(mr, dataset2, project_key)
            utils.register_uri_for_any_dataset_artifact_info_upload(mr, register_files=True)

            reply = listener.run_ad_hoc_test(client=client, params=params)
            assert isinstance(reply, websocket.RunAdHocTest)
            assert reply.results and 1 == len(reply.results)
            assert my_simple_test_debug_multiple_datasets.meta.uuid == reply.results[0].testUuid
            assert not reply.results[0].result.passed
            assert not reply.results[0].result.is_error
            assert reply.results[0].result.failed_indexes is not None
            assert 2 == len(reply.results[0].result.failed_indexes)
            assert str(enron_data.id) in reply.results[0].result.failed_indexes
            assert str(dataset2.id) in reply.results[0].result.failed_indexes
            assert 0 == reply.results[0].result.failed_indexes[str(enron_data.id)][0]
            assert 0 == reply.results[0].result.failed_indexes[str(dataset2.id)][0]


@test
def my_simple_test_legacy_debug_no_name(dataset: Dataset, debug: bool = False):
    output_ds = None
    if debug:
        output_ds = dataset.copy()
        output_ds.name = None
    return GiskardTestResult(passed=False, output_df=output_ds)


def test_websocket_actor_run_ad_hoc_test_legacy_debug_no_name(enron_data: Dataset):
    project_key = str(uuid.uuid4())

    with utils.MockedProjectCacheDir(project_key):
        utils.local_save_dataset_under_giskard_home_cache(enron_data, project_key)

        params = websocket.RunAdHocTestParam(
            testUuid=my_simple_test_legacy_debug_no_name.meta.uuid,
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
            projectKey="projectKey",
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            utils.register_uri_for_artifact_meta_info(mr, my_simple_test_legacy_debug_no_name, None)
            utils.register_uri_for_dataset_meta_info(mr, enron_data, project_key)
            utils.register_uri_for_any_dataset_artifact_info_upload(mr, register_files=True)

            # Dataset nullable name fixed in https://github.com/Giskard-AI/giskard/pull/1541
            reply = listener.run_ad_hoc_test(client=client, params=params)
            assert reply.results and 1 == len(reply.results)
            assert my_simple_test_legacy_debug_no_name.meta.uuid == reply.results[0].testUuid
            assert not reply.results[0].result.passed
            assert not reply.results[0].result.is_error
            assert reply.results[0].result.failed_indexes


def test_websocket_actor_run_test_suite():
    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=my_simple_test.meta.uuid,
                ),
                websocket.SuiteTestArgument(
                    id=1,
                    testUuid=my_simple_test_successful.meta.uuid,
                ),
                websocket.SuiteTestArgument(
                    id=2,
                    testUuid=my_simple_test_error.meta.uuid,
                ),
            ],
            globalArguments=[],
        )
        utils.register_uri_for_artifact_meta_info(mr, my_simple_test, None)
        utils.register_uri_for_artifact_meta_info(mr, my_simple_test_successful, None)
        utils.register_uri_for_artifact_meta_info(mr, my_simple_test_error, None)

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert not reply.is_error
        assert not reply.is_pass
        assert 3 == len(reply.results)
        assert 0 == reply.results[0].id
        assert not reply.results[0].result.is_error
        assert not reply.results[0].result.passed
        assert 1 == reply.results[1].id
        assert not reply.results[1].result.is_error
        assert reply.results[1].result.passed
        assert 2 == reply.results[2].id
        assert reply.results[2].result.is_error
        assert not reply.results[2].result.passed


def test_websocket_actor_run_test_suite_share_models_and_dataset_instance():
    def random_prediction(df):
        return [random.randint(0, 9) for _ in df.index]

    # Use random model to ensure model prediction cache is shared (same instance loaded)
    random_model = giskard.Model(random_prediction, "regression", feature_names=["feature"])
    mock_dataset = giskard.Dataset(pd.DataFrame({"feature": range(100)}))

    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=same_prediction.meta.uuid,
                    arguments=[
                        websocket.FuncArgument(
                            name="left",
                            model=websocket.ArtifactRef(project_key="project_key", id=str(random_model.id)),
                            none=False,
                        ),
                        websocket.FuncArgument(
                            name="right",
                            model=websocket.ArtifactRef(project_key="project_key", id=str(random_model.id)),
                            none=False,
                        ),
                        websocket.FuncArgument(
                            name="ds",
                            dataset=websocket.ArtifactRef(project_key="project_key", id=str(mock_dataset.id)),
                            none=False,
                        ),
                    ],
                ),
                websocket.SuiteTestArgument(
                    id=1,
                    testUuid=same_prediction.meta.uuid,
                    arguments=[
                        websocket.FuncArgument(
                            name="left",
                            model=websocket.ArtifactRef(project_key="project_key", id=str(random_model.id)),
                            none=False,
                        )
                    ],
                ),
                websocket.SuiteTestArgument(
                    id=2,
                    testUuid=same_prediction.meta.uuid,
                    arguments=[
                        websocket.FuncArgument(
                            name="right",
                            model=websocket.ArtifactRef(project_key="project_key", id=str(random_model.id)),
                            none=False,
                        )
                    ],
                ),
                websocket.SuiteTestArgument(id=2, testUuid=same_prediction.meta.uuid, arguments=[]),
            ],
            globalArguments=[
                websocket.FuncArgument(
                    name="left",
                    model=websocket.ArtifactRef(project_key="project_key", id=str(random_model.id)),
                    none=False,
                ),
                websocket.FuncArgument(
                    name="right",
                    model=websocket.ArtifactRef(project_key="project_key", id=str(random_model.id)),
                    none=False,
                ),
                websocket.FuncArgument(
                    name="ds",
                    dataset=websocket.ArtifactRef(project_key="project_key", id=str(mock_dataset.id)),
                    none=False,
                ),
            ],
        )
        utils.register_uri_for_artifact_meta_info(mr, same_prediction, None)

        utils.register_uri_for_model_meta_info(mr, random_model, "project_key")
        utils.register_uri_for_model_artifact_info(mr, random_model, "project_key", register_file_contents=True)

        utils.register_uri_for_dataset_meta_info(mr, mock_dataset, "project_key")
        utils.register_uri_for_dataset_artifact_info(mr, mock_dataset, "project_key", register_file_contents=True)

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert not reply.is_error
        assert reply.is_pass
        assert 4 == len(reply.results)


def test_websocket_actor_run_test_suite_raise_error():
    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=my_simple_test.meta.uuid,
                ),
            ],
            globalArguments=[],
        )
        # The test is not registerd, will raise error when downloading

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert reply.is_error
        assert not reply.is_pass
        assert 0 == len(reply.results)


MY_TEST_DEFAULT_VALUE = 1
MY_TEST_INPUT_VALUE = 2
MY_TEST_GLOBAL_VALUE = 3
MY_TEST_KWARGS_VALUE = 4


@test
def my_test_return(value: int = MY_TEST_DEFAULT_VALUE):
    # Return the passed value in message
    return GiskardTestResult(passed=False, messages=[TestMessage(TestMessageLevel.INFO, text=str(value))])


def test_websocket_actor_run_test_suite_with_global_arguments():
    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=my_test_return.meta.uuid,
                    arguments=[],
                ),
            ],
            globalArguments=[
                websocket.FuncArgument(name="value", int=MY_TEST_GLOBAL_VALUE, none=False),
            ],
        )
        utils.register_uri_for_artifact_meta_info(mr, my_test_return, None)

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert not reply.is_error
        assert not reply.is_pass
        assert 1 == len(reply.results)
        assert 0 == reply.results[0].id
        assert not reply.results[0].result.passed
        assert 1 == len(reply.results[0].result.messages)
        # Globals fill the missing
        assert str(MY_TEST_GLOBAL_VALUE) == reply.results[0].result.messages[0].text
        assert 1 == len(reply.results[0].arguments)
        assert (
            "value" == reply.results[0].arguments[0].name
            and MY_TEST_GLOBAL_VALUE == reply.results[0].arguments[0].int_arg
        )


def test_websocket_actor_run_test_suite_with_test_input():
    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=my_test_return.meta.uuid,
                    arguments=[websocket.FuncArgument(name="value", int=MY_TEST_INPUT_VALUE, none=False)],
                ),
            ],
            globalArguments=[
                websocket.FuncArgument(name="value", int=MY_TEST_GLOBAL_VALUE, none=False),
            ],
        )
        utils.register_uri_for_artifact_meta_info(mr, my_test_return, None)

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert not reply.is_error
        assert not reply.is_pass
        assert 1 == len(reply.results)
        assert 0 == reply.results[0].id
        assert not reply.results[0].result.passed
        assert 1 == len(reply.results[0].result.messages)
        # Globals will not replace test input
        assert str(MY_TEST_INPUT_VALUE) == reply.results[0].result.messages[0].text
        assert 1 == len(reply.results[0].arguments)
        assert (
            "value" == reply.results[0].arguments[0].name
            and MY_TEST_INPUT_VALUE == reply.results[0].arguments[0].int_arg
        )


def test_websocket_actor_run_test_suite_with_legacy_debug():
    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=my_simple_test__legacy_debug.meta.uuid,
                    arguments=[
                        websocket.FuncArgument(name="value", int=MY_TEST_INPUT_VALUE, none=False),
                    ],
                ),
            ],
            globalArguments=[
                websocket.FuncArgument(name="value", int=MY_TEST_GLOBAL_VALUE, none=False),
            ],
        )
        utils.register_uri_for_artifact_meta_info(mr, my_simple_test__legacy_debug, None)
        utils.register_uri_for_any_dataset_artifact_info_upload(mr, True)

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert not reply.is_error, reply.logs
        assert reply.is_pass

        assert 1 == len(reply.results)
        assert 0 == reply.results[0].id
        assert reply.results[0].result.passed


def test_websocket_actor_run_test_suite_with_kwargs():
    with utils.MockedClient(mock_all=False) as (client, mr):
        params = websocket.TestSuiteParam(
            projectKey=str(uuid.uuid4()),
            tests=[
                websocket.SuiteTestArgument(
                    id=0,
                    testUuid=my_test_return.meta.uuid,
                    arguments=[
                        websocket.FuncArgument(name="value", int=MY_TEST_INPUT_VALUE, none=False),
                        websocket.FuncArgument(
                            name="kwargs", kwargs=f"kwargs['value'] = {MY_TEST_KWARGS_VALUE}", none=False
                        ),
                    ],
                ),
            ],
            globalArguments=[
                websocket.FuncArgument(name="value", int=MY_TEST_GLOBAL_VALUE, none=False),
            ],
        )
        utils.register_uri_for_artifact_meta_info(mr, my_test_return, None)

        reply = listener.run_test_suite(client, params)

        assert isinstance(reply, websocket.TestSuite)
        assert not reply.is_error
        assert not reply.is_pass
        assert 1 == len(reply.results)
        assert 0 == reply.results[0].id
        assert not reply.results[0].result.passed
        assert 1 == len(reply.results[0].result.messages)
        # Kwargs will replace test input
        assert str(MY_TEST_KWARGS_VALUE) == reply.results[0].result.messages[0].text
        assert 1 == len(reply.results[0].arguments)
        assert (
            "value" == reply.results[0].arguments[0].name
            and MY_TEST_KWARGS_VALUE == reply.results[0].arguments[0].int_arg
        )
