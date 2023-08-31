import logging
import random
import secrets
import stomp
import time
from pydantic import AnyHttpUrl
from websocket._exceptions import WebSocketException, WebSocketBadStatusException

import giskard
from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.testing.registry.registry import load_plugins
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
    token_file_location: str
    ws_conn: stomp.WSStompConnection
    ws_stopping: bool = False
    ws_attempts: int = 0
    ws_max_attemps: int = 10
    ws_max_reply_payload_size: int = 8192
    ml_worker_id: str
    client: GiskardClient

    def __init__(self, is_server=False, backend_url: AnyHttpUrl = None, api_key=None, hf_token=None) -> None:
        client = None if is_server else GiskardClient(backend_url, api_key, hf_token)
        self.client = client

        ws_conn = self._create_websocket_client(backend_url, is_server, hf_token)

        if not is_server:
            logger.info("Remote server host and port are specified, connecting as an external ML Worker")

        self.ws_conn = ws_conn

    def _create_websocket_client(self, backend_url: AnyHttpUrl = None, is_server=False, hf_token=None):
        from giskard.ml_worker.websocket.listener import MLWorkerWebSocketListener

        if is_server:
            # Retrieve from settings for internal ML Worker
            self.ml_worker_id = INTERNAL_WORKER_ID
            backend_url = AnyHttpUrl(
                url=f"http://{settings.host}:{settings.ws_port}/{settings.ws_path}",  # noqa NOSONAR - we don't actually use http here
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
            # Use 443 port if https and no given port
            if backend_url.scheme == "https" and backend_url.port is None:
                backend_url.port = 443
        ws_conn = stomp.WSStompConnection(
            [(backend_url.host, backend_url.port)],
            ws_path=backend_url.path,
            reconnect_attempts_max=1,  # Reconnection managed by our Listener
            header={"COOKIE": f"spaces-jwt={hf_token};" if hf_token else ""},  # To access a private HF Spaces
        )
        if backend_url.scheme == "https":
            # Enable SSL/TLS
            ws_conn.set_ssl([(backend_url.host, backend_url.port)])
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
            time.sleep(1 + random.random() * 2)  # noqa NOSONAR - we won't be affected by the waiting time
            self.ws_attempts += 1
            logger.debug(f"Disconnected due to {e}, reconnecting...")
            self.connect_websocket_client()
        else:
            self.ws_attempts = 0

    def _connect_websocket_client(self, is_server=False):
        if self.ws_stopping:
            return

        try:
            if not is_server:
                # External ML Worker: use API key
                self.ws_conn.connect(
                    with_connect_command=True,
                    wait=False,
                    headers={
                        "api-key": self.client.session.auth.token,
                    },
                )
            else:
                # Internal ML Worker
                internal_ml_worker_token = secrets.token_hex(16)
                with open(f"{settings.home_dir / 'run' / 'internal-ml-worker'}", "w") as f:
                    f.write(internal_ml_worker_token)
                self.ws_conn.connect(
                    with_connect_command=True,
                    wait=False,
                    headers={
                        "token": internal_ml_worker_token,
                    },
                )
        except (WebSocketException, WebSocketBadStatusException) as e:
            logger.warn(f"Connection to Giskard Backend failed: {e.__class__.__name__}")
            if isinstance(e, WebSocketBadStatusException):
                if e.status_code == 404:
                    # Backend may need upgrade or private HF Spaces
                    logger.error(
                        f"Please make sure that the version of Giskard server is above '{giskard.__version__}'"
                    )
                else:
                    logger.error(
                        f"WebSocket connection error {e.status_code}: "
                        f"Please make sure that you are using {settings.ws_path} as the WebSocket endpoint"
                    )
                self.stop()

    def is_remote_worker(self):
        return self.ml_worker_id is not INTERNAL_WORKER_ID

    async def start(self):
        load_plugins()

        if self.ws_conn:
            self.ws_stopping = False
            self.connect_websocket_client()

        while not self.ws_stopping:
            global websocket_loop_callback
            try:
                if websocket_loop_callback:
                    websocket_loop_callback()
            except TypeError as e:
                # Catch TypeError due to an issue in stompy.py
                # as described in https://github.com/jasonrbriggs/stomp.py/issues/424
                # and https://github.com/websocket-client/websocket-client/issues/930
                logger.warn(f"WebSocket connection may not be properly closed: {e}")

    def stop(self):
        if self.ws_conn:
            self.ws_stopping = True
            self.ws_conn.disconnect()
