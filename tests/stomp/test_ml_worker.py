from typing import Callable, List

import asyncio
import json

import pytest
import requests_mock
from websockets.server import WebSocketServerProtocol, serve

from giskard.ml_worker.ml_worker import MLWorker
from giskard.ml_worker.stomp.constants import UTF_8, HeaderType, StompCommand
from giskard.ml_worker.stomp.parsing import Frame, StompFrame
from giskard.ml_worker.websocket.action import MLWorkerAction


@pytest.fixture(scope="function")
def patch_settings():
    from copy import deepcopy

    from giskard.settings import settings

    old_settings = deepcopy(settings.dict())
    override = {"ws_port": 6789, "ws_path": "", "host": "127.0.0.1", "disable_analytics": True}
    for k, v in override.items():
        setattr(settings, k, v)
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
                frame = StompFrame.from_string(await asyncio.wait_for(websocket.recv(), timeout=1))
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
                    "id": str(i),
                    "action": MLWorkerAction.getInfo.name,
                    "param": {"list_packages": True, "bla": 1, "bli": [True]},
                }
            ),
        )
        for i in range(10)
    ]


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_ml_worker(requests_mock: requests_mock.Mocker, patch_settings: None):
    worker = MLWorker(is_server=True)
    # Make sure settings are patched
    assert worker._host_url == "ws://127.0.0.1:6789"
    received_frames: List[Frame] = []
    expected_commands = [StompCommand.CONNECT, StompCommand.SUBSCRIBE, StompCommand.SUBSCRIBE]
    requests_mock.get("http://127.0.0.1:6789/public-api/ml-worker-connect", json={})

    async with serve(
        wrapped_handler(received_frames, info_frame),
        host="127.0.0.1",
        port=6789,
    ):
        await asyncio.wait_for(worker.start(nb_workers=1, restart=False), timeout=60)
    # assert len(received_frames) == len(expected_commands)
    for i, frame in enumerate(received_frames):
        if i < len(expected_commands):
            assert frame.command == expected_commands[i]
        elif i == (len(received_frames) - 1):
            assert frame.command == StompCommand.DISCONNECT
        else:
            assert frame.command == StompCommand.SEND
            payload = json.loads(frame.body)
            assert "error_str" not in payload
