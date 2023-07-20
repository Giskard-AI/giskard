import logging

import random
import stomp
import time

from pydantic import AnyHttpUrl

from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.testing.registry.registry import load_plugins
from giskard.ml_worker.websocket.listener import MLWorkerWebSocketListener
from giskard.settings import settings

logger = logging.getLogger(__name__)

INTERNAL_WORKER_ID = "INTERNAL"
EXTERNAL_WORKER_ID = "EXTERNAL"

websocket_loop_callback: callable = None


def websocket_use_main_thread(callback):
    # Expose and run the WebSocket loop in main thread
    global websocket_loop_callback
    websocket_loop_callback = callback
    return "WebSocket ML Worker loop"


class MLWorker:
    socket_file_location: str
    ws_conn: stomp.WSStompConnection
    ws_stopping: bool = False
    ws_attempts: int = 0
    ws_max_attemps: int = 10
    ml_worker_id: str
    client: GiskardClient

    def __init__(self, is_server=False, backend_url: AnyHttpUrl = None, api_key=None) -> None:
        client = None if is_server else GiskardClient(backend_url, api_key)
        self.client = client

        ws_conn = self._create_websocket_client(backend_url, is_server)

        if not is_server:
            logger.info("Remote server host and port are specified, connecting as an external ML Worker")

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
        ws_conn = stomp.WSStompConnection(
            [(backend_url.host, backend_url.port)],
            ws_path=backend_url.path,
            reconnect_attempts_max=1,  # Reconnection managed by our Listener
        )
        ws_conn.transport.override_threading(websocket_use_main_thread)  # Expose WebSocket loop function to ML Worker
        ws_conn.set_listener("ml-worker-action-listener", MLWorkerWebSocketListener(self))
        return ws_conn

    def connect_websocket_client(self):
        if self.ws_attempts >= self.ws_max_attemps:
            logger.warn("Maximum reconnection attemps reached, please retry.")
            # Exit the process
            self.stop()
            return
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
                wait=False,
                headers={
                    "jwt": self.client.session.auth.token,
                },
            )
        else:
            # Internal ML Worker: TODO: use a token from env
            self.ws_conn.connect(
                with_connect_command=True,
                wait=False,
                headers={
                    "token": "inoki-test-token",
                },
            )

    def is_remote_worker(self):
        return self.ml_worker_id is not INTERNAL_WORKER_ID

    async def start(self):
        load_plugins()

        if self.ws_conn:
            self.ws_stopping = False
            self.connect_websocket_client()

        while not self.ws_stopping:
            global websocket_loop_callback
            if websocket_loop_callback:
                websocket_loop_callback()

    async def stop(self):
        if self.ws_conn:
            self.ws_stopping = True
            self.ws_conn.disconnect()
