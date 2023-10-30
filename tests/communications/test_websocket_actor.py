import uuid
import pytest
import pandas as pd
import shutil

import requests_mock

from giskard.datasets.base import Dataset
from giskard.ml_worker import ml_worker, websocket
from giskard.ml_worker.utils.file_utils import get_file_name
from giskard.ml_worker.websocket import listener
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base.model import BaseModel
from giskard.settings import settings
from giskard import slicing_function, transformation_function

from tests import utils


NOT_USED_WEBSOCKET_ACTOR = [
    MLWorkerAction.generateQueryBasedSlicingFunction,
]


def test_all_registered_websocket_actor():
    # Any actor except not used should not be the default one
    for action in MLWorkerAction:
        if action not in NOT_USED_WEBSOCKET_ACTOR:
            assert listener.WEBSOCKET_ACTORS[action.name] != listener.websocket_log_actor


def test_websocket_actor_echo():
    msg = websocket.EchoMsg(msg="echo")
    reply = listener.echo(msg)
    assert isinstance(reply, websocket.EchoMsg)
    assert reply.msg == msg.msg


def test_websocket_actor_get_info():
    internal_ml_worker = utils.MockedWebSocketMLWorker(is_server=True)    # Internal worker
    external_ml_worker = utils.MockedWebSocketMLWorker(is_server=False)   # External worker

    without_package_params = websocket.GetInfoParam(list_packages=False)
    with_package_params = websocket.GetInfoParam(list_packages=True)

    # Internal worker, without packages
    server_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(internal_ml_worker),
        params=without_package_params,
    )
    assert isinstance(server_ml_worker_info, websocket.GetInfo)
    assert not server_ml_worker_info.isRemote
    assert server_ml_worker_info.mlWorkerId == ml_worker.INTERNAL_WORKER_ID
    assert 0 == len(server_ml_worker_info.installedPackages.values())

    # Internal worker, with packages
    server_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(internal_ml_worker),
        params=with_package_params,
    )
    assert isinstance(server_ml_worker_info, websocket.GetInfo)
    assert not server_ml_worker_info.isRemote
    assert server_ml_worker_info.mlWorkerId == ml_worker.INTERNAL_WORKER_ID
    assert 0 != len(server_ml_worker_info.installedPackages.values())

    # External worker, without packages
    remote_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(external_ml_worker),
        params=without_package_params,
    )
    assert isinstance(remote_ml_worker_info, websocket.GetInfo)
    assert remote_ml_worker_info.isRemote
    assert remote_ml_worker_info.mlWorkerId == ml_worker.EXTERNAL_WORKER_ID
    assert 0 == len(remote_ml_worker_info.installedPackages.values())

    # External worker, with packages
    remote_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(external_ml_worker),
        params=with_package_params,
    )
    assert isinstance(remote_ml_worker_info, websocket.GetInfo)
    assert remote_ml_worker_info.isRemote
    assert remote_ml_worker_info.mlWorkerId == ml_worker.EXTERNAL_WORKER_ID
    assert 0 != len(remote_ml_worker_info.installedPackages.values())


def test_websocket_actor_stop_worker():
    reply = listener.on_ml_worker_stop_worker()
    assert isinstance(reply, websocket.Empty)


def test_websocket_actor_get_catalog():
    catalog = listener.get_catalog()

    assert catalog.tests is not None
    for t in catalog.tests.values():
        assert t.code is not None
        # The filter condition
        assert t.type == "TEST"
        assert "giskard" in t.tags

    assert catalog.slices is not None
    for s in catalog.slices.values():
        assert s.code is not None
        # The filter condition
        assert s.type == "SLICE"
        assert "giskard" in t.tags

    assert catalog.transformations is not None
    for t in catalog.transformations.values():
        assert t.code is not None
        # The filter condition
        assert t.type == "TRANSFORMATION"
        assert "giskard" in t.tags


@pytest.mark.parametrize("data,model,sample", [
    ("enron_data", "enron_model", False),
    ("enron_data", "enron_model", True),
    ("enron_data", "enron_model", None),
    ("hotel_text_data", "hotel_text_model", False)
])
def test_websocket_actor_run_model_internal(data, model, sample, request):
    dataset: Dataset = request.getfixturevalue(data)
    model: BaseModel = request.getfixturevalue(model)

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests
    inspection_id = 0

    with utils.MockedProjectCacheDir(project_key):
        # Prepare dataset and model
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        params = websocket.RunModelParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id), sample=sample),
            inspectionId=inspection_id,
            project_key=project_key,
        )
        # Internal worker does not have client
        reply = listener.run_model(client=None, params=params)
        assert isinstance(reply, websocket.Empty)
        # Inspection are logged locally
        inspection_path = settings.home_dir / "projects" / project_key / "models" / "inspections" / str(inspection_id)
        assert (inspection_path / get_file_name("predictions", "csv", sample)).exists()
        assert (inspection_path / get_file_name("calculated", "csv", sample)).exists()
        # Clean up
        shutil.rmtree(inspection_path, ignore_errors=True)


@pytest.mark.parametrize("data,model,sample", [
    ("enron_data", "enron_model", False),
    ("enron_data", "enron_model", True),
    ("enron_data", "enron_model", None),
    ("hotel_text_data", "hotel_text_model", False)
])
@pytest.mark.slow
def test_websocket_actor_run_model(data, model, sample, request):
    dataset: Dataset = request.getfixturevalue(data)
    model: BaseModel = request.getfixturevalue(model)

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests
    inspection_id = 0

    with utils.MockedProjectCacheDir(project_key):
        params = websocket.RunModelParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id), sample=sample),
            inspectionId=inspection_id,
            project_key=project_key,
        )

        with utils.MockedClient(mock_all=False) as (client, mr):
            # Prepare URL for meta info
            utils.register_uri_for_model_meta_info(mr, model, project_key)
            utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)
            utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)
            utils.register_uri_for_dataset_artifact_info(mr, dataset, project_key, register_file_contents=True)
            # Prepare URL for inspections
            utils.register_uri_for_inspection(mr, project_key, inspection_id, sample)

            # Internal worker does not have client
            reply = listener.run_model(client=client, params=params)
            assert isinstance(reply, websocket.Empty)


@pytest.mark.parametrize("internal", [
    True, False
])
def test_websocket_actor_run_model_for_data_frame_regression(internal, request):
    dataset: Dataset = request.getfixturevalue("hotel_text_data")
    model: BaseModel = request.getfixturevalue("hotel_text_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key), utils.MockedClient(mock_all=False) as (client, mr):
        # Prepare model
        if internal:
            utils.local_save_model_under_giskard_home_cache(model, project_key)
        else:
            utils.register_uri_for_model_meta_info(mr, model, project_key)
            utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)

        # Prepare dataframe
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in row.items()
                }) for _, row in dataset.df.iterrows()
            ],
        )

        # Prepare parameters
        params = websocket.RunModelForDataFrameParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
        )

        # client
        reply = listener.run_model_for_data_frame(client=None if internal else client, params=params)
        assert isinstance(reply, websocket.RunModelForDataFrame)
        assert not reply.all_predictions
        assert reply.prediction
        assert reply.raw_prediction
        assert not reply.probabilities


@pytest.mark.parametrize("internal", [
    True, False
])
def test_websocket_actor_run_model_for_data_frame_classification(internal, request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    model: BaseModel = request.getfixturevalue("enron_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key), utils.MockedClient(mock_all=False) as (client, mr):
        # Prepare model
        if internal:
            utils.local_save_model_under_giskard_home_cache(model, project_key)
        else:
            utils.register_uri_for_model_meta_info(mr, model, project_key)
            utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)

        # Prepare dataframe
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in row.items()
                }) for _, row in dataset.df.iterrows()
            ],
        )

        # Prepare parameters
        params = websocket.RunModelForDataFrameParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
        )

        # client
        reply = listener.run_model_for_data_frame(client=None if internal else client, params=params)
        assert isinstance(reply, websocket.RunModelForDataFrame)
        assert reply.all_predictions
        assert reply.prediction
        assert not reply.raw_prediction
        assert not reply.probabilities


@pytest.mark.parametrize("data,model", [
    ("enron_data", "enron_model"),
    ("hotel_text_data", "hotel_text_model")
])
def test_websocket_actor_explain_ws_internal(data, model, request):
    dataset: Dataset = request.getfixturevalue(data)
    model: BaseModel = request.getfixturevalue(model)

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key):
        # Prepare model and dataset
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        params = websocket.ExplainParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            columns={str(k): str(v) for k, v in next(dataset.df.iterrows())[1].items()},  # Pick the first row
        )
        reply = listener.explain_ws(client=None, params=params)
        assert isinstance(reply, websocket.Explain)


@pytest.mark.parametrize("data,model", [
    ("enron_data", "enron_model"),
    ("hotel_text_data", "hotel_text_model")
])
@pytest.mark.slow
def test_websocket_actor_explain_ws(data, model, request):
    dataset: Dataset = request.getfixturevalue(data)
    model: BaseModel = request.getfixturevalue(model)

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key), utils.MockedClient(mock_all=False) as (client, mr):
        # Prepare model and dataset
        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)
        utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)
        utils.register_uri_for_dataset_artifact_info(mr, dataset, project_key, register_file_contents=True)

        params = websocket.ExplainParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            columns={str(k): str(v) for k, v in next(dataset.df.iterrows())[1].items()},  # Pick the first row
        )
        reply = listener.explain_ws(client=client, params=params)
        assert isinstance(reply, websocket.Explain)


@pytest.mark.parametrize("internal", [
    True, False
])
def test_websocket_actor_explain_text_ws_regression(internal, request):
    dataset: Dataset = request.getfixturevalue("hotel_text_data")
    model: BaseModel = request.getfixturevalue("hotel_text_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key), utils.MockedClient(mock_all=False) as (client, mr):
        # Prepare model and dataset
        if internal:
            utils.local_save_model_under_giskard_home_cache(model, project_key)
        else:
            utils.register_uri_for_model_meta_info(mr, model, project_key)
            utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)

        text_feature_name = None
        for col_name, col_type in dataset.column_types.items():
            if col_type == "text":
                text_feature_name = col_name
                break
        assert text_feature_name

        params = websocket.ExplainTextParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            feature_name=text_feature_name,
            columns={str(k): str(v) for k, v in next(dataset.df.iterrows())[1].items()},  # Pick the first row
            column_types=dataset.column_types,
        )
        reply = listener.explain_text_ws(client=None if internal else client, params=params)
        assert isinstance(reply, websocket.ExplainText)
        # Regression text explaining: Giskard Hub uses "WEIGHTS" to show it
        assert "WEIGHTS" in reply.weights.keys()


@pytest.mark.parametrize("internal", [
    True, False
])
def test_websocket_actor_explain_text_ws_classification(internal, request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    model: BaseModel = request.getfixturevalue("enron_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key), utils.MockedClient(mock_all=False) as (client, mr):
        # Prepare model and dataset
        if internal:
            utils.local_save_model_under_giskard_home_cache(model, project_key)
        else:
            utils.register_uri_for_model_meta_info(mr, model, project_key)
            utils.register_uri_for_model_artifact_info(mr, model, project_key, register_file_contents=True)


        text_feature_name = None
        for col_name, col_type in dataset.column_types.items():
            if col_type == "text":
                text_feature_name = col_name
                break
        assert text_feature_name

        params = websocket.ExplainTextParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            feature_name=text_feature_name,
            columns={str(k): str(v) for k, v in next(dataset.df.iterrows())[1].items()},  # Pick the first row
            column_types=dataset.column_types,
        )
        reply = listener.explain_text_ws(client=None if internal else client, params=params)
        assert isinstance(reply, websocket.ExplainText)
        # Classification labels
        for label in model.meta.classification_labels:
            assert label in reply.weights.keys()


def test_websocket_actor_dataset_processing_empty_internal(request):
    dataset: Dataset = request.getfixturevalue("enron_data")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key):
        # Prepare dataset
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        # FIXME: functions can be None from the protocol, but not iterable
        # params = websocket.DatasetProcessingParam(
        #     dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id), sample=False),
        #     functions=None,
        # )
        params = websocket.DatasetProcessingParam(
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id), sample=False),
            functions=[],
        )
        reply = listener.dataset_processing(client=None, params=params)
        assert isinstance(reply, websocket.DatasetProcessing)
        assert reply.datasetId == str(dataset.id)
        assert reply.totalRows == len(list(dataset.df.index))   
        # No line filtered
        assert reply.filteredRows is not None and 0 == len(reply.filteredRows)
        # No line modified
        assert reply.modifications is not None and 0 == len(reply.modifications)


# Define a slicing function
@slicing_function(row_level=False)
def head_slice(df: pd.DataFrame) -> pd.DataFrame:
    return df.head(1)


@pytest.mark.parametrize("callable_under_project", [
    False, True
])
def test_websocket_actor_dataset_processing_head_slicing_with_cache(callable_under_project, request):
    dataset: Dataset = request.getfixturevalue("enron_data")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests
    callable_function_project_key = project_key if callable_under_project else None

    with utils.MockedProjectCacheDir(project_key):
        # Prepare dataset
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        head_slice.meta.uuid = str(uuid.uuid4())

        params = websocket.DatasetProcessingParam(
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id), sample=False),
            functions=[
                websocket.DatasetProcessingFunction(
                    slicingFunction=websocket.ArtifactRef(
                        project_key=callable_function_project_key,
                        id=head_slice.meta.uuid,
                    )
                )
            ],
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            # Prepare URL for meta info
            cf = head_slice
            # The slicing function will be loaded from the current module, without further requests
            utils.register_uri_for_artifact_meta_info(mr, cf, project_key=callable_function_project_key)
            utils.register_uri_for_artifact_info(mr, cf, project_key=callable_function_project_key)

            # The dataset can be then loaded from the cache, without further requests
            utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

            reply = listener.dataset_processing(client=client, params=params)
            assert isinstance(reply, websocket.DatasetProcessing)
            assert reply.datasetId == str(dataset.id)
            assert reply.totalRows == len(list(dataset.df.index))   
            # One line not filtered
            assert reply.filteredRows is not None and reply.totalRows - 1 == len(reply.filteredRows)
            # No line modified
            assert reply.modifications is not None and 0 == len(reply.modifications)


# Define a transformation function
@transformation_function()
def do_nothing(row):
    return row


@pytest.mark.parametrize("callable_under_project", [
    False, True
])
def test_websocket_actor_dataset_processing_do_nothing_transform_with_cache(callable_under_project, request):
    dataset: Dataset = request.getfixturevalue("enron_data")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    with utils.MockedProjectCacheDir(project_key):
        # Prepare dataset
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)
        callable_function_project_key = project_key if callable_under_project else None

        do_nothing.meta.uuid = str(uuid.uuid4())

        params = websocket.DatasetProcessingParam(
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id), sample=False),
            functions=[
                websocket.DatasetProcessingFunction(
                    transformationFunction=websocket.ArtifactRef(
                        project_key=callable_function_project_key,
                        id=do_nothing.meta.uuid,
                    )
                )
            ],
        )
        with utils.MockedClient(mock_all=False) as (client, mr):
            # Prepare URL for meta info
            cf = do_nothing
            # The slicing function will be loaded from the current module, without further requests
            utils.register_uri_for_artifact_meta_info(mr, cf, project_key=callable_function_project_key)
            utils.register_uri_for_artifact_info(mr, cf, project_key=callable_function_project_key)

            # The dataset can be then loaded from the cache, without further requests
            utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

            reply = listener.dataset_processing(client=client, params=params)
            assert isinstance(reply, websocket.DatasetProcessing)
            assert reply.datasetId == str(dataset.id)
            assert reply.totalRows == len(list(dataset.df.index))   
            # No line filtered
            assert reply.filteredRows is not None and 0 == len(reply.filteredRows)
            # No line modified
            assert reply.modifications is not None and 0 == len(reply.modifications)
