from typing import Any, Callable, Dict, List

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
import requests_mock
import yaml
from pandas import DataFrame
from websockets.server import WebSocketServerProtocol, serve

from giskard import Model
from giskard.cli_utils import validate_url
from giskard.client.dtos import ModelMetaInfo
from giskard.datasets.base import Dataset
from giskard.ml_worker.ml_worker import MLWorker
from giskard.ml_worker.stomp.constants import UTF_8, HeaderType, StompCommand
from giskard.ml_worker.stomp.parsing import Frame, StompFrame
from giskard.ml_worker.websocket import ArtifactRef
from giskard.ml_worker.websocket import DataFrame as GiskardDataFrame
from giskard.ml_worker.websocket import (
    DataRow,
    ExplainParam,
    RunAdHocTestParam,
    RunModelForDataFrameParam,
    RunModelParam,
)
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base.model import META_FILENAME
from giskard.settings import Settings


@pytest.fixture(scope="function")
def patch_settings() -> Settings:
    from copy import deepcopy

    from giskard.settings import settings

    with tempfile.TemporaryDirectory(prefix="giskard-home-") as f:
        old_settings = deepcopy(settings.dict())
        override = {
            "ws_port": 6789,
            "ws_path": "",
            "host": "127.0.0.1",
            "disable_analytics": True,
            "use_pool": False,
            "home": f,
        }
        for k, v in override.items():
            setattr(settings, k, v)
        assert not settings.use_pool
        yield settings
        for k, v in old_settings.items():
            setattr(settings, k, v)


def wrapped_handler(received_messages: List[Frame], to_send: Callable[[str], List[Frame]], **kwargs):
    async def handler(websocket: WebSocketServerProtocol):
        frame = StompFrame.from_string(await websocket.recv())
        received_messages.append(frame)
        # First, should receive CONNECT
        assert frame.command == StompCommand.CONNECT
        await websocket.send(
            StompFrame.CONNECTED.build_frame({HeaderType.VERSION: "1.2"}).to_bytes(),
        )

        # Then the subscribes
        frame = StompFrame.from_string(await websocket.recv())
        received_messages.append(frame)
        assert frame.command == StompCommand.SUBSCRIBE
        assert frame.headers[HeaderType.DESTINATION] == "/ml-worker/EXTERNAL/action"
        action_id = frame.headers[HeaderType.ID]

        frame = StompFrame.from_string(await websocket.recv())
        received_messages.append(frame)
        assert frame.command == StompCommand.SUBSCRIBE
        assert frame.headers[HeaderType.DESTINATION] == "/ml-worker/EXTERNAL/config"

        # Send some message
        for frame in to_send(action_id, **kwargs):
            await websocket.send(frame.to_bytes())

        # Ensure you get some answers
        try:
            while True:
                frame = StompFrame.from_string(await asyncio.wait_for(websocket.recv(), timeout=10))
                received_messages.append(frame)
                assert frame.command == StompCommand.SEND
        except asyncio.TimeoutError:
            pass

        # Ask to stop the worker
        await websocket.send(
            StompFrame.MESSAGE.build_frame(
                {
                    HeaderType.DESTINATION: "/dest",
                    HeaderType.SUBSCRIPTION: action_id,
                    HeaderType.MESSAGE_ID: "ans-id1",
                },
                body=json.dumps(
                    {
                        "id": "stopping",
                        "action": MLWorkerAction.stopWorker.name,
                        "param": {},
                    }
                ),
            )
            .to_bytes()
            .decode(UTF_8)
        )
        # Ensure you get the STOP worker message
        frame = StompFrame.from_string(await websocket.recv())
        received_messages.append(frame)
        assert frame.command == StompCommand.SEND
        # Ensure you get the disconnect message, and then stop
        frame = StompFrame.from_string(await websocket.recv())
        received_messages.append(frame)
        assert frame.command == StompCommand.DISCONNECT

    return handler


def info_frame(action_id: str):
    return [
        StompFrame.MESSAGE.build_frame(
            {
                HeaderType.DESTINATION: "/dest",
                HeaderType.SUBSCRIPTION: action_id,
                HeaderType.MESSAGE_ID: "ans-id1",
                HeaderType.CONTENT_TYPE: "application/json",
            },
            body=json.dumps(
                {
                    "id": "info_frame",
                    "action": MLWorkerAction.getInfo.name,
                    "param": {"list_packages": True},
                }
            ),
        )
    ]


def ensure_config_worker(requests_mock: requests_mock.Mocker) -> MLWorker:
    worker = MLWorker(is_server=False, backend_url=validate_url(None, None, "http://127.0.0.1:6789"))
    # Make sure settings are patched
    assert worker._host_url == "ws://127.0.0.1:6789"
    requests_mock.get("http://127.0.0.1:6789/public-api/ml-worker-connect", json={})
    return worker


def ensure_run_worker(received_frames: List[Frame]) -> MLWorker:
    expected_commands = [StompCommand.CONNECT, StompCommand.SUBSCRIBE, StompCommand.SUBSCRIBE]
    # Make sure we receive connect, subscribe *2, then only send and disconnect at the ent
    for i, frame in enumerate(received_frames):
        if i < len(expected_commands):
            assert frame.command == expected_commands[i]
        elif i == (len(received_frames) - 1):
            assert frame.command == StompCommand.DISCONNECT
        else:
            # Ensure every send does not contains a error in payload
            assert frame.command == StompCommand.SEND
            payload = json.loads(frame.body)["payload"]
            assert "error_str" not in payload


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_ml_worker_get_info(requests_mock: requests_mock.Mocker, patch_settings: Settings):
    received_frames: List[Frame] = []
    worker = ensure_config_worker(requests_mock)
    async with serve(
        wrapped_handler(received_frames, info_frame),
        host=patch_settings.host,
        port=patch_settings.ws_port,
    ):
        await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
        ensure_run_worker(received_frames)


def snake_to_camelcase(name):
    parts = name.split("_")
    return "".join(parts[:1] + [p.capitalize() for p in parts[1:]])


@pytest.fixture(scope="function")
def remote_titanic_dataset(patch_settings: Settings, titanic_dataset: Dataset, requests_mock: requests_mock.Mocker):
    with tempfile.TemporaryDirectory(prefix="giskard-dataset-") as fd:
        dataset_dir = Path(fd)
        titanic_dataset.save(dataset_dir, titanic_dataset.id.hex)
        artifacts_dataset = list(dataset_dir.glob("*"))
        filenames_dataset = [f.name for f in artifacts_dataset]

        with (dataset_dir / "giskard-dataset-meta.yaml").open() as meta_dataset:
            parsed_meta_dataset: Dict[str, Any] = yaml.unsafe_load(meta_dataset)

        for name in list(parsed_meta_dataset.keys()):
            parsed_meta_dataset[snake_to_camelcase(name)] = parsed_meta_dataset.pop(name)

        # Mock artifact info
        requests_mock.get(
            f"http://{patch_settings.host}:{patch_settings.ws_port}/api/v2/artifact-info/test-ml-worker-key/datasets/{titanic_dataset.id.hex}",
            json=filenames_dataset,
        )
        # Mock artifacts
        for filename in filenames_dataset:
            requests_mock.get(
                f"http://{patch_settings.host}:{patch_settings.ws_port}/api/v2/artifacts/test-ml-worker-key/datasets/{titanic_dataset.id.hex}/{filename}",
                content=(dataset_dir / filename).read_bytes(),
            )

        # Mock dataset metadata
        # Note : meta is not validated with pydantic
        requests_mock.get(
            f"http://{patch_settings.host}:{patch_settings.ws_port}/api/v2/project/test-ml-worker-key/datasets/{titanic_dataset.id.hex}",
            json=parsed_meta_dataset,
        )
        yield titanic_dataset.id.hex


@pytest.fixture
def remote_titanic_model(
    patch_settings: Settings,
    titanic_model: Model,
    requests_mock: requests_mock.Mocker,
):
    model_id = uuid4().hex
    with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
        temp_dir = Path(f)
        titanic_model.save(temp_dir)
        artifacts = list(temp_dir.glob("*"))
        filenames = [f.name for f in artifacts]
        requests_mock.get(
            f"http://{patch_settings.host}:{patch_settings.ws_port}/api/v2/artifact-info/test-ml-worker-key/models/{model_id}",
            json=filenames,
        )
        for filename in filenames:
            requests_mock.get(
                f"http://{patch_settings.host}:{patch_settings.ws_port}/api/v2/artifacts/test-ml-worker-key/models/{model_id}/{filename}",
                content=(temp_dir / filename).read_bytes(),
            )
        with (temp_dir / META_FILENAME).open() as meta:
            parsed_meta: Dict[str, Any] = yaml.unsafe_load(meta)
        for name in list(parsed_meta.keys()):
            parsed_meta[snake_to_camelcase(name)] = parsed_meta.pop(name)
        for name in ["loaderClass", "loaderModule"]:
            parsed_meta.pop(name)
        parsed_meta["projectId"] = 1
        parsed_meta["createdDate"] = "toto"
        parsed_meta["id"] = model_id
        requests_mock.get(
            f"http://{patch_settings.host}:{patch_settings.ws_port}/api/v2/project/test-ml-worker-key/models/{model_id}",
            json=parsed_meta,
        )
        yield model_id


def run_model_frame(action_id: str, dataset_id: str, model_id: str):
    return [
        StompFrame.MESSAGE.build_frame(
            {
                HeaderType.DESTINATION: "/dest",
                HeaderType.SUBSCRIPTION: action_id,
                HeaderType.MESSAGE_ID: "ans-id1",
                HeaderType.CONTENT_TYPE: "application/json",
            },
            body=json.dumps(
                {
                    "id": "run_model_frame",
                    "action": MLWorkerAction.runModel.name,
                    "param": RunModelParam(
                        model=ArtifactRef(project_key="test-ml-worker-key", id=model_id),
                        dataset=ArtifactRef(project_key="test-ml-worker-key", id=dataset_id),
                        inspectionId=2,
                        project_key="test-ml-worker-key",
                    ).dict(by_alias=True),
                }
            ),
        )
    ]


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_ml_worker_model_run(
    requests_mock: requests_mock.Mocker,
    patch_settings: Settings,
    remote_titanic_dataset: str,
    remote_titanic_model: str,
):
    dataset_uuid = remote_titanic_dataset
    model_uuid = remote_titanic_model
    received_frames: List[Frame] = []
    worker = ensure_config_worker(requests_mock)

    mock_pred = requests_mock.post(
        "http://127.0.0.1:6789/api/v2/artifacts/test-ml-worker-key/models/inspections/2/predictions.csv",
        json={},
    )
    mock_calculated = requests_mock.post(
        "http://127.0.0.1:6789/api/v2/artifacts/test-ml-worker-key/models/inspections/2/calculated.csv",
        json={},
    )

    async with serve(
        wrapped_handler(received_frames, run_model_frame, dataset_id=dataset_uuid, model_id=model_uuid),
        host=patch_settings.host,
        port=patch_settings.ws_port,
    ):
        await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
        ensure_run_worker(received_frames)
    assert mock_pred.called
    assert mock_pred.call_count == 1
    assert mock_calculated.called
    assert mock_calculated.call_count == 1
    # TODO:  validate content ?


def run_model_frame_dataframe(action_id: str, df: DataFrame, model_id: str):
    dtypes = df.dtypes.astype(str).to_dict()
    mapping = {"int64": "numeric", "float64": "numeric", "object": "category"}
    types = {k: mapping[v] for k, v in dtypes.items()}
    gsk_df = GiskardDataFrame(rows=[DataRow(columns=row.astype(str).to_dict()) for _, row in df.iterrows()])
    return [
        StompFrame.MESSAGE.build_frame(
            {
                HeaderType.DESTINATION: "/dest",
                HeaderType.SUBSCRIPTION: action_id,
                HeaderType.MESSAGE_ID: "ans-id1",
                HeaderType.CONTENT_TYPE: "application/json",
            },
            body=json.dumps(
                {
                    "id": "run_model_dataframe_frame",
                    "action": MLWorkerAction.runModelForDataFrame.name,
                    "param": RunModelForDataFrameParam(
                        model=ArtifactRef(project_key="test-ml-worker-key", id=model_id),
                        dataframe=gsk_df,
                        column_dtypes=dtypes,
                        column_types=types,
                    ).dict(by_alias=True),
                }
            ),
        )
    ]


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_ml_worker_model_run_dataframe(
    requests_mock: requests_mock.Mocker,
    patch_settings: Settings,
    titanic_model_data_raw,
    remote_titanic_model: str,
):
    _, df = titanic_model_data_raw
    model_uuid = remote_titanic_model
    received_frames: List[Frame] = []
    worker = ensure_config_worker(requests_mock)

    async with serve(
        wrapped_handler(received_frames, run_model_frame_dataframe, df=df, model_id=model_uuid),
        host=patch_settings.host,
        port=patch_settings.ws_port,
    ):
        await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
        ensure_run_worker(received_frames)
    # TODO: validate output ?


def run_model_explain(action_id: str, dataset_id: str, model_id: str, df: DataFrame):
    _, data = next(df.iterrows())
    return [
        StompFrame.MESSAGE.build_frame(
            {
                HeaderType.DESTINATION: "/dest",
                HeaderType.SUBSCRIPTION: action_id,
                HeaderType.MESSAGE_ID: "ans-id1",
                HeaderType.CONTENT_TYPE: "application/json",
            },
            body=json.dumps(
                {
                    "id": "explain_frame",
                    "action": MLWorkerAction.explain.name,
                    "param": ExplainParam(
                        model=ArtifactRef(project_key="test-ml-worker-key", id=model_id),
                        dataset=ArtifactRef(project_key="test-ml-worker-key", id=dataset_id),
                        columns=data.astype(str).to_dict(),
                    ).dict(by_alias=True),
                }
            ),
        )
    ]


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_ml_worker_explain(
    requests_mock: requests_mock.Mocker,
    patch_settings: Settings,
    titanic_model_data_raw,
    remote_titanic_dataset: str,
    remote_titanic_model: str,
):
    _, df = titanic_model_data_raw
    model_uuid = remote_titanic_model
    dataset_uuid = remote_titanic_dataset
    received_frames: List[Frame] = []
    worker = ensure_config_worker(requests_mock)

    async with serve(
        wrapped_handler(received_frames, run_model_explain, df=df, model_id=model_uuid, dataset_id=dataset_uuid),
        host=patch_settings.host,
        port=patch_settings.ws_port,
    ):
        await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
        ensure_run_worker(received_frames)
    # TODO: validate output ?
    return
