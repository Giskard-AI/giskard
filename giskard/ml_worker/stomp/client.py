from typing import Callable, Dict, List, Optional, Set

import asyncio
import logging
from abc import abstractmethod
from urllib.parse import urlparse

from websockets.client import WebSocketClientProtocol, connect
from websockets.exceptions import ConnectionClosed

from giskard.ml_worker.stomp.constants import HeaderType, StompCommand
from giskard.ml_worker.stomp.parsing import Frame, FrameParser, StompFrame, StompProtocolError

LOGGER = logging.getLogger(__name__)


class StompClientError(RuntimeError):
    pass


class StompWSClient:
    def __init__(
        self, url: str, additional_headers: Dict[str, str], http_headers: Optional[Dict[str, str]] = None
    ) -> None:
        self._host_url = url
        self._host_part = urlparse(url).netloc
        self._receiver_queue: asyncio.Queue[Frame] = asyncio.Queue()
        self._sender_queue: asyncio.Queue[Frame] = asyncio.Queue()
        self._additional_headers = additional_headers
        self._subscriptions: Dict[str, Callable] = {}
        self._is_stopping = False
        self._connect_headers = http_headers

    async def _receiver(self, websocket: WebSocketClientProtocol):
        async for message in websocket:
            if self._is_stopping:
                return
            try:
                frame = StompFrame.from_string(message)
                await self._receiver_queue.put(frame)
                LOGGER.debug("Received frame %s", frame)
            except StompProtocolError as e:
                LOGGER.error("Error when parsing message %s", message)
                LOGGER.exception(e)

    async def _sender(self, websocket: WebSocketClientProtocol):
        # We send the remaining message before stopping
        while not self._sender_queue.empty() or not self._is_stopping:
            frame = await self._sender_queue.get()
            await websocket.send(frame.to_bytes())

    async def _send_frame(self, websocket: WebSocketClientProtocol, frame: Frame):
        LOGGER.debug("Sending frame...")
        LOGGER.debug(frame.to_bytes())
        if not StompFrame[frame.command].is_client_command():
            raise StompClientError(f"Should only send client type frame, got {frame.command}")
        await websocket.send(frame.to_bytes())

    async def _frame_handler(self):
        pending = set()
        while not self._is_stopping:
            # If the queue is not empty, get all the elements and start the coroutine
            # Also, if we don't have anything pending, we wait on the queue
            while not self._receiver_queue.empty() or len(pending) == 0:
                frame = await self._receiver_queue.get()
                pending.add(asyncio.create_task(self._process_frame(frame)))

            # Wait a bit and check what is done
            # We want to be done asap, since we'll keep checking on it
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED, timeout=0.01)
            for task in done:
                # Now we can await it, since it's done
                frames = await task
                # Add the frames to send back
                for frame in frames:
                    await self._sender_queue.put(frame)
            # Handle disconnect frame
            if self._is_stopping:
                await self._sender_queue.put(StompFrame.DISCONNECT.build_frame({}))

    async def _process_frame(self, frame: Frame) -> List[Frame]:
        subscription = frame.headers[HeaderType.SUBSCRIPTION]
        if subscription not in self._subscriptions:
            raise StompClientError(f"Unknown subscription {subscription}")
        result = await self._subscriptions[subscription](frame)
        return result

    @abstractmethod
    async def setup(self, websocket: WebSocketClientProtocol):
        raise NotImplementedError()

    async def _connect(self, websocket):
        LOGGER.info("Sending CONNECT frame...")
        await self._send_frame(
            websocket,
            StompFrame.CONNECT.build_frame(
                {
                    HeaderType.ACCEPT_VERSION: "1.2",
                    HeaderType.HEART_BEAT: "0,0",
                    HeaderType.HOST: self._host_part,
                    **self._additional_headers,
                },
            ),
        )

    async def unsubscribe(self, websocket, id_sub):
        if id_sub not in self._subscriptions:
            raise StompClientError("Cannot un-subscribe unknown id")
        del self._subscriptions[id_sub]
        return await self._send_frame(
            websocket,
            StompFrame.UNSUBSCRIBE.build_frame(
                {
                    HeaderType.ID: id_sub,
                }
            ),
        )

    async def subscribe(self, websocket, destination, id_sub, handler):
        if id_sub in self._subscriptions:
            raise StompClientError("Cannot subscribe with the same id several times")
        self._subscriptions[id_sub] = handler
        return await self._send_frame(
            websocket,
            StompFrame.SUBSCRIBE.build_frame(
                {
                    HeaderType.DESTINATION: destination,
                    HeaderType.ID: id_sub,
                }
            ),
        )

    async def _handle_connect(self, websocket: WebSocketClientProtocol):
        LOGGER.debug("Sending CONNECT...")
        await self._connect(websocket)
        LOGGER.debug("Waiting for CONNECTED...")
        message = await asyncio.wait_for(websocket.recv(), timeout=30)

        frame: Frame = FrameParser.parse(message)
        LOGGER.debug("Received %s", frame)

        if frame.command != StompCommand.CONNECTED:
            raise StompProtocolError(f"Should have CONNECTED, got {frame}")

    async def _handle_partial_end(self, done: Set[asyncio.Task], pending: Set[asyncio.Task]):
        # If we are stopping,
        # we let other stuff finish, ie sending last disconnect frame and so on.
        if self._is_stopping:
            other_done, pending = await asyncio.wait(pending, return_when=asyncio.ALL_COMPLETED, timeout=5)
            for t in other_done:
                done.add(t)
        # If there are still pending task, cancel them
        for task in pending:
            task.cancel()
        # If there are any error, then raise the first one encountered
        for task in done:
            exception = task.exception()
            if exception is not None:
                raise exception

    async def start(self, restart=False):
        # For look to ensure for reconnection
        LOGGER.info("Connecting to %s", self._host_url)
        async for websocket in connect(self._host_url, extra_headers=self._connect_headers):
            LOGGER.info("Connected !")
            try:
                await self._handle_connect(websocket)
                # In case of re-connection, let's redo the subscription
                for sub_id in list(self._subscriptions.keys()):
                    await self.unsubscribe(websocket, sub_id)
                # First, do the setup
                await self.setup(websocket)
                # Then starts consumer and producer
                # https://websockets.readthedocs.io/en/stable/howto/patterns.html#consumer-and-producer
                consumer_task = asyncio.create_task(self._receiver(websocket=websocket))
                producer_task = asyncio.create_task(self._sender(websocket=websocket))
                handler_task = asyncio.create_task(self._frame_handler())

                done, pending = await asyncio.wait(
                    [consumer_task, producer_task, handler_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                await self._handle_partial_end(done, pending)
            except ConnectionClosed as e:
                LOGGER.warning("Connection closed", exc_info=1)
                # Raise only if we should not restart
                if not self._is_stopping and not restart:
                    raise RuntimeError("Connection closed") from e
            # In case on normal disconnect from the server, check if we should reconnect or not
            if not restart or self._is_stopping:
                return

    def stop(self):
        self._is_stopping = True
