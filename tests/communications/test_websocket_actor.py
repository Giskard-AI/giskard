import uuid
import pytest

from giskard.datasets.base import Dataset
from giskard.ml_worker import ml_worker, websocket
from giskard.ml_worker.utils.file_utils import get_file_name
from giskard.ml_worker.websocket import listener
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base.model import BaseModel
from giskard.settings import settings

from tests.utils import MockedWebSocketMLWorker
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
    internal_ml_worker = MockedWebSocketMLWorker(is_server=True)    # Internal worker
    external_ml_worker = MockedWebSocketMLWorker(is_server=False)   # External worker

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
    # Inspection
    inspection_path = settings.home_dir / "projects" / project_key / "models" / "inspections" / str(inspection_id)
    assert (inspection_path / get_file_name("predictions", "csv", sample)).exists()
    assert (inspection_path / get_file_name("calculated", "csv", sample)).exists()


def test_websocket_actor_run_model_for_data_frame_regression_internal(request):
    dataset: Dataset = request.getfixturevalue("hotel_text_data")
    model: BaseModel = request.getfixturevalue("hotel_text_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    # Prepare model
    utils.local_save_model_under_giskard_home_cache(model, project_key)

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
    reply = listener.run_model_for_data_frame(client=None, params=params)
    assert isinstance(reply, websocket.RunModelForDataFrame)
    assert not reply.all_predictions
    assert reply.prediction
    assert reply.raw_prediction
    assert not reply.probabilities


def test_websocket_actor_run_model_for_data_frame_classification_internal(request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    model: BaseModel = request.getfixturevalue("enron_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    # Prepare model
    utils.local_save_model_under_giskard_home_cache(model, project_key)

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
    reply = listener.run_model_for_data_frame(client=None, params=params)
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


def test_websocket_actor_explain_text_ws_regression_internal(request):
    dataset: Dataset = request.getfixturevalue("hotel_text_data")
    model: BaseModel = request.getfixturevalue("hotel_text_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    # Prepare model and dataset
    utils.local_save_model_under_giskard_home_cache(model, project_key)

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
    reply = listener.explain_text_ws(client=None, params=params)
    assert isinstance(reply, websocket.ExplainText)
    # Regression text explaining: Giskard Hub uses "WEIGHTS" to show it
    assert "WEIGHTS" in reply.weights.keys()


def test_websocket_actor_explain_text_ws_classification_internal(request):
    dataset: Dataset = request.getfixturevalue("enron_data")
    model: BaseModel = request.getfixturevalue("enron_model")

    project_key = str(uuid.uuid4()) # Use a UUID to separate the resources used by the tests

    # Prepare model and dataset
    utils.local_save_model_under_giskard_home_cache(model, project_key)

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
    reply = listener.explain_text_ws(client=None, params=params)
    assert isinstance(reply, websocket.ExplainText)
    # Classification labels
    for label in model.meta.classification_labels:
        assert label in reply.weights.keys()
