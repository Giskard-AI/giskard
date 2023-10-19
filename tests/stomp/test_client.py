from typing import List

import asyncio

import pytest
from websockets.client import WebSocketClientProtocol
from websockets.server import WebSocketServerProtocol, serve

from giskard.ml_worker.stomp.client import StompClientError, StompWSClient
from giskard.ml_worker.stomp.constants import HeaderType, StompCommand
from giskard.ml_worker.stomp.parsing import Frame, StompFrame

WS_URL = "ws://127.0.0.1:6789"


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_setup():
    req_list = [StompFrame.CONNECTED.build_frame({HeaderType.VERSION: "1.2"})]
    received_list: List[Frame] = []

    async def handler(websocket: WebSocketServerProtocol):
        while True:
            message = await websocket.recv()
            received_list.append(StompFrame.from_string(message))
            if len(req_list) > 0:
                await websocket.send(req_list.pop(0).to_bytes())
            # else:
            #     await websocket.close()

    async with serve(handler, host="127.0.0.1", port=6789):

        class TestClient(StompWSClient):
            nb_call = 0

            async def setup(self, websocket):
                self.nb_call += 1
                self.stop()

        client = TestClient(WS_URL, {})

        await client.start()
        assert client.nb_call == 1
        assert len(received_list) == 1
        assert received_list[0].command == StompCommand.CONNECT


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_subscribe():
    req_list = [
        StompFrame.CONNECTED.build_frame({HeaderType.VERSION: "1.2"}),
        StompFrame.MESSAGE.build_frame(
            {HeaderType.DESTINATION: "/dest", HeaderType.SUBSCRIPTION: "id1", HeaderType.MESSAGE_ID: "ans-id1"},
            body="Some content",
        ),
    ]
    received_list: List[Frame] = []

    async def handler(websocket: WebSocketServerProtocol):
        while True:
            message = await websocket.recv()
            received_list.append(StompFrame.from_string(message))
            if len(req_list) > 0:
                await websocket.send(req_list.pop(0).to_bytes())
            # else:
            #     await websocket.close()

    async with serve(handler, host="127.0.0.1", port=6789):

        class TestClient(StompWSClient):
            nb_call = 0

            async def handle_my_sub(self, frame: Frame) -> Frame:
                self.nb_call += 1
                assert frame.command == StompCommand.MESSAGE
                assert frame.body == b"Some content"
                self.stop()
                return [StompFrame.DISCONNECT.build_frame({})]

            async def setup(self, websocket: WebSocketClientProtocol):
                await self.subscribe(websocket, "/my-sub", "id1", self.handle_my_sub)

        client = TestClient(WS_URL, {})

        await asyncio.wait_for(client.start(), timeout=10)
        assert client.nb_call == 1
        assert len(received_list) == 3
        assert received_list[0].command == StompCommand.CONNECT
        assert received_list[1].command == StompCommand.SUBSCRIBE
        assert received_list[2].command == StompCommand.DISCONNECT


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_bad_subscription_should_raise():
    req_list = [
        StompFrame.CONNECTED.build_frame({HeaderType.VERSION: "1.2"}),
        StompFrame.MESSAGE.build_frame(
            {HeaderType.DESTINATION: "/dest", HeaderType.SUBSCRIPTION: "id2", HeaderType.MESSAGE_ID: "ans-id1"},
            body="Some content",
        ),
    ]

    async def handler(websocket: WebSocketServerProtocol):
        while True:
            await websocket.recv()
            if len(req_list) > 0:
                await websocket.send(req_list.pop(0).to_bytes())

    async with serve(handler, host="127.0.0.1", port=6789):

        class TestClient(StompWSClient):
            async def handle_my_sub(self, frame: Frame) -> Frame:
                return []

            async def setup(self, websocket: WebSocketClientProtocol):
                await self.subscribe(websocket, "/my-sub", "id1", self.handle_my_sub)

        client = TestClient(WS_URL, {})
        with pytest.raises(StompClientError) as exc_info:
            await asyncio.wait_for(client.start(), timeout=10)
        assert "Unknown subscription id2" in str(exc_info)


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_long_task_should_not_block():
    req_list = [
        StompFrame.CONNECTED.build_frame({HeaderType.VERSION: "1.2"}),
        StompFrame.MESSAGE.build_frame(
            {HeaderType.DESTINATION: "/dest", HeaderType.SUBSCRIPTION: "id1", HeaderType.MESSAGE_ID: "ans-id1"},
            body="Some content",
        ),
        StompFrame.MESSAGE.build_frame(
            {HeaderType.DESTINATION: "/dest", HeaderType.SUBSCRIPTION: "id1", HeaderType.MESSAGE_ID: "ans-id2"},
            body="Some content",
        ),
        StompFrame.MESSAGE.build_frame(
            {HeaderType.DESTINATION: "/dest", HeaderType.SUBSCRIPTION: "id1", HeaderType.MESSAGE_ID: "ans-id3"},
            body="Some content",
        ),
        StompFrame.MESSAGE.build_frame(
            {HeaderType.DESTINATION: "/dest", HeaderType.SUBSCRIPTION: "id1", HeaderType.MESSAGE_ID: "ans-id4"},
            body="Some content",
        ),
    ]
    received_list: List[Frame] = []

    async def handler(websocket: WebSocketServerProtocol):
        while True:
            message = await websocket.recv()
            received_list.append(StompFrame.from_string(message))
            while len(req_list) > 0:
                await websocket.send(req_list.pop(0).to_bytes())
                await asyncio.sleep(1)

    async with serve(handler, host="127.0.0.1", port=6789):

        class TestClient(StompWSClient):
            nb_call = 0

            async def handle_my_sub(self, frame: Frame) -> Frame:
                await asyncio.sleep(5)
                self.nb_call += 1
                await asyncio.sleep(180)
                assert frame.command == StompCommand.MESSAGE
                assert frame.body == b"Some content"
                self.stop()
                return [StompFrame.DISCONNECT.build_frame({})]

            async def setup(self, websocket: WebSocketClientProtocol):
                await self.subscribe(websocket, "/my-sub", "id1", self.handle_my_sub)

        client = TestClient(WS_URL, {})

        with pytest.raises(asyncio.exceptions.TimeoutError):
            await asyncio.wait_for(client.start(), timeout=10)
        assert client.nb_call == 4
        assert len(received_list) == 2
        assert received_list[0].command == StompCommand.CONNECT
        assert received_list[1].command == StompCommand.SUBSCRIBE
