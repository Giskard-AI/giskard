from typing import Callable, List

import asyncio
import json
import sys
import tempfile
from pathlib import Path

import pytest
import requests_mock
import yaml
from websockets.server import WebSocketServerProtocol, serve

from giskard import Model
from giskard.ml_worker.ml_worker import MLWorker
from giskard.ml_worker.stomp.constants import UTF_8, HeaderType, StompCommand
from giskard.ml_worker.stomp.parsing import Frame, StompFrame
from giskard.ml_worker.websocket import ArtifactRef, RunAdHocTestParam, RunModelParam
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base.model import META_FILENAME


@pytest.fixture(scope="function")
def patch_settings():
    from copy import deepcopy

    from giskard.settings import settings

    old_settings = deepcopy(settings.dict())
    override = {"ws_port": 6789, "ws_path": "", "host": "127.0.0.1", "disable_analytics": True, "use_pool": False}
    for k, v in override.items():
        setattr(settings, k, v)
    assert not settings.use_pool
    yield
    for k, v in old_settings.items():
        setattr(settings, k, v)


def wrapped_handler(received_messages: List[Frame], to_send: Callable[[str], List[Frame]]):
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
        assert frame.headers[HeaderType.DESTINATION] == "/ml-worker/INTERNAL/action"
        action_id = frame.headers[HeaderType.ID]

        frame = StompFrame.from_string(await websocket.recv())
        received_messages.append(frame)
        assert frame.command == StompCommand.SUBSCRIBE
        assert frame.headers[HeaderType.DESTINATION] == "/ml-worker/INTERNAL/config"

        # Send some message
        for frame in to_send(action_id):
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
                    "param": {"list_packages": True, "bla": 1, "bli": [True]},
                }
            ),
        )
    ]


def ensure_config_worker(requests_mock: requests_mock.Mocker) -> MLWorker:
    worker = MLWorker(is_server=True)
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


@pytest.mark.skipif(condition=sys.platform == "win32", reason="Pytest stays hanging")
@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_ml_worker_get_info(requests_mock: requests_mock.Mocker, patch_settings: None):
    received_frames: List[Frame] = []
    worker = ensure_config_worker(requests_mock)
    async with serve(
        wrapped_handler(received_frames, info_frame),
        host="127.0.0.1",
        port=6789,
    ):
        await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
        ensure_run_worker(received_frames)


def run_model_frame(action_id: str):
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
                        model=ArtifactRef(project_key="titanic", id="titanic"),
                        dataset=ArtifactRef(project_key="titanic", id="titanic"),
                        inspectionId=2,
                        project_key="titanic",
                    ).dict(by_alias=True),
                }
            ),
        )
    ]


@pytest.mark.skipif(condition=sys.platform == "win32", reason="Pytest stays hanging")
@pytest.mark.concurrency
@pytest.mark.asyncio
@pytest.mark.skipif(True, "Do not work, because worker pool is not mocked")
async def test_ml_worker_model_run(requests_mock: requests_mock.Mocker, patch_settings: None, titanic_model: Model):
    received_frames: List[Frame] = []
    worker = ensure_config_worker(requests_mock)
    with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
        titanic_model.save(f)
        temp_dir = Path(f)
        artifacts = list(temp_dir.glob("*"))
        filenames = [f.name for f in artifacts]
        print(artifacts)
        print(filenames)

        requests_mock.get("http://127.0.0.1:6789/api/v2/artifact-info/titanic/models/titanic", json=filenames)
        with (temp_dir / META_FILENAME).open() as meta:
            requests_mock.get(
                "http://127.0.0.1:6789/api/v2/project/titanic/models/titanic", json=yaml.unsafe_load(meta)
            )

        # META_FILENAME
        for filename in filenames:
            requests_mock.get(
                f"http://127.0.0.1:6789/api/v2/artifact-info/titanic/models/titanic/${filename}",
                body=(temp_dir / filename).open(),
            )

        # requests_mock.get("http://127.0.0.1:6789/api/v2/artifacts/titanic/models/titanic/titanic", body=fp)
        async with serve(
            wrapped_handler(received_frames, run_model_frame),
            host="127.0.0.1",
            port=6789,
        ):
            await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
            ensure_run_worker(received_frames)
