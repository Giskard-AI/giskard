import asyncio
import json
from time import sleep
from unittest.mock import patch

import pytest
from websockets.server import WebSocketServerProtocol, serve

from giskard.ml_worker.stomp.constants import UTF_8, HeaderType, StompCommand
from giskard.ml_worker.stomp.parsing import StompFrame
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.ml_worker.websocket.listener import websocket_actor


def long_action(*args, **kwargs):
    sleep(180)
    return "OK"


def stop_worker(*args, **kwargs):
    return StompFrame.DISCONNECT.build_frame({})


@pytest.mark.concurrency
@pytest.mark.asyncio
@pytest.mark.skip("Not working for now")
async def test_ml_worker():
    async def handler(websocket: WebSocketServerProtocol):
        message = await websocket.recv()
        assert StompFrame.from_string(message).command == StompCommand.CONNECT
        await websocket.send(
            StompFrame.CONNECTED.build_frame({HeaderType.VERSION: "1.2"}).to_bytes(),
        )

        message = await websocket.recv()
        frame = StompFrame.from_string(message)
        assert frame.command == StompCommand.SUBSCRIBE
        assert frame.headers[HeaderType.DESTINATION] == "/ml-worker/INTERNAL/action"
        action_id = frame.headers[HeaderType.ID]

        message = await websocket.recv()
        frame = StompFrame.from_string(message)
        assert frame.command == StompCommand.SUBSCRIBE
        assert frame.headers[HeaderType.DESTINATION] == "/ml-worker/INTERNAL/config"

        for i in range(10):
            await websocket.send(
                StompFrame.MESSAGE.build_frame(
                    {
                        HeaderType.DESTINATION: "/dest",
                        HeaderType.SUBSCRIPTION: action_id,
                        HeaderType.MESSAGE_ID: "ans-id1",
                    },
                    body=json.dumps(
                        {"id": str(i), "action": MLWorkerAction.getInfo.name, "params": {"bla": 1, "bli": [True]}}
                    ),
                )
                .to_bytes()
                .decode(UTF_8)
            )

        await websocket.send(
            StompFrame.MESSAGE.build_frame(
                {
                    HeaderType.DESTINATION: "/dest",
                    HeaderType.SUBSCRIPTION: action_id,
                    HeaderType.MESSAGE_ID: "ans-id1",
                },
                body=json.dumps({"id": "deco", "action": MLWorkerAction.stopWorker.name}),
            )
            .to_bytes()
            .decode(UTF_8)
        )

        while True:
            message = await websocket.recv()

    with patch("giskard.ml_worker.ml_worker.settings") as settings_mock:
        settings_mock.ws_port = 6789
        settings_mock.ws_path = ""
        settings_mock.host = "127.0.0.1"
        settings_mock.disable_analytics = True

        from giskard.ml_worker.ml_worker import WEBSOCKET_ACTORS, MLWorker

        for k in list(WEBSOCKET_ACTORS.keys()):
            del WEBSOCKET_ACTORS[k]
        assert len(WEBSOCKET_ACTORS) == 0

        websocket_actor(MLWorkerAction.getInfo)(long_action)
        websocket_actor(MLWorkerAction.stopWorker, execute_in_pool=False)(stop_worker)

        assert len(WEBSOCKET_ACTORS) == 2
        worker = MLWorker(is_server=True)
        assert worker._host_url == "ws://127.0.0.1:6789"

        async with serve(handler, host="127.0.0.1", port=6789):
            await asyncio.wait_for(worker.start(nb_workers=1), timeout=30)
