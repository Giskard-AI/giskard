import asyncio
import logging
import sys

import random
import stomp
import time

import grpc
from grpc.aio._server import Server
from pydantic import AnyHttpUrl

from giskard import cli_utils
from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.bridge.ml_worker_bridge import MLWorkerBridge
from giskard.ml_worker.testing.registry.registry import load_plugins
from giskard.ml_worker.utils.request_interceptor import MLWorkerRequestInterceptor
from giskard.ml_worker.websocket.listener import MLWorkerWebSocketListener
from giskard.settings import settings

logger = logging.getLogger(__name__)

INTERNAL_WORKER_ID = "INTERNAL"
EXTERNAL_WORKER_ID = "EXTERNAL"


class MLWorker:
    socket_file_location: str
    tunnel: MLWorkerBridge = None
    grpc_server: Server
    ws_conn: stomp.WSStompConnection
    ws_stopping: bool = False
    ws_attempts: int = 0
    ws_max_attemps: int = 10
    ml_worker_id: str
    client: GiskardClient

    def __init__(self, is_server=False, backend_url: AnyHttpUrl = None, api_key=None) -> None:
        client = None if is_server else GiskardClient(backend_url, api_key)
        self.client = client

        server, address = self._create_grpc_server(client, is_server)
        ws_conn = self._create_websocket_client(backend_url, is_server)

        if not is_server:
            logger.info("Remote server host and port are specified, connecting as an external ML Worker")
            self.tunnel = MLWorkerBridge(address, client)

        self.grpc_server = server
        self.ws_conn = ws_conn

    def _create_websocket_client(self, backend_url: AnyHttpUrl = None, is_server=False):
        if is_server:
            # Retrieve from settings for internal ML Worker
            self.ml_worker_id = INTERNAL_WORKER_ID
            backend_url = AnyHttpUrl(
                url=f"http://{settings.host}:{settings.ws_port}/{settings.ws_path}",
                scheme="http",
                host=settings.host,
                port=settings.ws_port,
                path=settings.ws_path,
            )
        else:
            # External ML worker: URL should be provided
            self.ml_worker_id = EXTERNAL_WORKER_ID
            # Use the URL path component provided by settings
            backend_url.path = settings.ws_path
        ws_conn = stomp.WSStompConnection([(backend_url.host, backend_url.port)], ws_path=backend_url.path)
        ws_conn.set_listener("ml-worker-action-listener", MLWorkerWebSocketListener(self))
        return ws_conn

    def connect_websocket_client(self):
        if self.ws_attempts >= self.ws_max_attemps:
            logger.warn("Maximum reconnection attemps reached, please retry.")
            return  # TODO: Exit the process
        try:
            self._connect_websocket_client(self.ml_worker_id == INTERNAL_WORKER_ID)
        except Exception as e:
            time.sleep(1 + random.random() * 2)
            self.ws_attempts += 1
            logger.debug(f"Disconnected due to {e}, reconnecting...")
            self.connect_websocket_client()
        else:
            self.ws_attempts = 0

    def _connect_websocket_client(self, is_server=False):
        if self.ws_stopping:
            return

        if not is_server:
            # External ML Worker: use jwt token
            # raise ConnectFailedException
            self.ws_conn.connect(
                with_connect_command=True,
                wait=True,
                headers={
                    "jwt": self.client.session.auth.token,
                },
            )
        else:
            # Internal ML Worker: TODO: use a token from env
            self.ws_conn.connect(
                with_connect_command=True,
                wait=True,
                headers={
                    "token": "inoki-test-token",
                },
            )

        if self.ws_conn.is_connected():
            self.ws_conn.subscribe(f"/ml-worker/{self.ml_worker_id}/action", f"ws-worker-{self.ml_worker_id}")
        else:
            raise Exception("Worker cannot connect through WebSocket")

    def _create_grpc_server(self, client: GiskardClient, is_server=False):
        from giskard.ml_worker.generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server
        from giskard.ml_worker.server.ml_worker_service import MLWorkerServiceImpl
        from giskard.ml_worker.utils.network import find_free_port

        server = grpc.aio.server(
            interceptors=[MLWorkerRequestInterceptor()],
            options=[
                ("grpc.max_send_message_length", settings.max_send_message_length_mb * 1024**2),
                ("grpc.max_receive_message_length", settings.max_receive_message_length_mb * 1024**2),
            ],
        )

        if is_server:
            port = settings.port if settings.port else find_free_port()
            address = f"{settings.host}:{port}"
        else:
            worker_id = cli_utils.ml_worker_id(is_server, client.host_url)
            # On Windows, we cannot use Unix sockets, so we use TCP.
            # Port 40052 is only used internally between the worker and the bridge.
            if sys.platform == "win32":
                # Find random open port
                port = find_free_port()
                address = f"localhost:{port}"
            else:
                self.socket_file_location = f"{settings.home_dir / 'run' / f'ml-worker-{worker_id}.sock'}"
                address = f"unix://{self.socket_file_location}"

        add_MLWorkerServicer_to_server(MLWorkerServiceImpl(self, client, address, not is_server), server)
        server.add_insecure_port(address)
        logger.info(f"Started ML Worker server on {address}")
        logger.debug(f"ML Worker settings: {settings}")
        return server, address

    async def start(self):
        load_plugins()

        if self.ws_conn:
            self.ws_stopping = False
            self.connect_websocket_client()

        await self.grpc_server.start()
        if self.tunnel:
            await self.tunnel.start()
        await self.grpc_server.wait_for_termination()

        for t in asyncio.all_tasks():
            if t != asyncio.current_task():
                await t

    async def stop(self):
        if self.tunnel:
            await self.tunnel.stop()
        if self.ws_conn:
            self.ws_stopping = True
            self.ws_conn.disconnect()
        await self.grpc_server.stop(3)
