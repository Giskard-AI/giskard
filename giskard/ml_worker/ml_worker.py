from typing import List, Optional, Union

import logging
import math
from uuid import UUID

from pydantic import AnyHttpUrl
from websockets.client import WebSocketClientProtocol

from giskard.cli_utils import validate_url
from giskard.core.validation import ConfiguredBaseModel
from giskard.ml_worker.stomp.client import StompWSClient
from giskard.ml_worker.stomp.constants import HeaderType
from giskard.ml_worker.stomp.parsing import Frame, StompFrame
from giskard.ml_worker.websocket.action import ActionPayload, ConfigPayload, MLWorkerAction
from giskard.ml_worker.websocket.listener import WEBSOCKET_ACTORS
from giskard.ml_worker.websocket.utils import fragment_message
from giskard.registry.registry import load_plugins
from giskard.settings import settings
from giskard.utils import shutdown_pool, start_pool
from giskard.utils.analytics_collector import analytics

LOGGER = logging.getLogger(__name__)

MAX_STOMP_ML_WORKER_REPLY_SIZE = 1500


class FragmentedPayload(ConfiguredBaseModel):
    id: UUID
    action: str
    payload: str
    f_index: int
    f_count: int


class MLWorker(StompWSClient):
    def __init__(
        self,
        worker_name,
        backend_url: AnyHttpUrl = None,
        api_key: Optional[str] = None,
        hf_token: Optional[str] = None,
    ) -> None:
        headers = {}
        connect_headers = {"COOKIE": f"spaces-jwt={hf_token};"} if hf_token is not None else None

        # External ML worker: URL should be provided
        self._worker_name = worker_name
        headers["api-key"] = api_key

        # Use the URL path component provided by settings
        if backend_url.port is not None:
            port = backend_url.port
        elif backend_url.scheme == "https":
            port = 443
        else:
            port = 80
        backend_url = validate_url(None, None, f"{backend_url.scheme}://{backend_url.host}:{port}{settings.ws_path}")
        ws_str = f"{'ws' if backend_url.scheme == 'http' else 'wss'}://{backend_url.host}:{port}{settings.ws_path}"

        super().__init__(ws_str, headers, connect_headers)
        self._backend_url = f"{backend_url.scheme}://{backend_url.host}:{port}"
        self._ws_max_reply_payload_size = MAX_STOMP_ML_WORKER_REPLY_SIZE
        self._api_key = api_key
        self._hf_token = hf_token

    async def config_handler(self, frame: Frame) -> List[Frame]:
        payload = ConfigPayload.parse_raw(frame.body)
        self._ws_max_reply_payload_size = max(MAX_STOMP_ML_WORKER_REPLY_SIZE, payload.value)
        LOGGER.info("MAX_STOMP_ML_WORKER_REPLY_SIZE set to %s", self._ws_max_reply_payload_size)

        return []

    async def action_handler(self, frame: Frame) -> List[Frame]:
        data = ActionPayload.parse_raw(frame.body)
        logging.info("Running job %s: %s", data.id, data.action.name)

        # Dispatch the action
        client_params = {
            "url": self._backend_url,
            "key": self._api_key,
            "hf_token": self._hf_token,
        }
        if data.action == MLWorkerAction.stopWorker:
            LOGGER.info("Marking worker as stopping...")
            self.stop()

        payload: Optional[Union[str, Frame]] = await WEBSOCKET_ACTORS[data.action.name](
            data, client_params, self._worker_name
        )
        # If no rep_id
        if payload is None:
            return []
        # We want to be able to send directly frame also (ie, disconnect frame for example)
        if isinstance(payload, Frame):
            return [payload]

        # Else we do the chunking thing (should be handled by websocket protocol transport, but nevermind)
        frag_count = math.ceil(len(payload) / self._ws_max_reply_payload_size)
        analytics.track(
            "mlworker:websocket:action:reply",
            {
                "name": data.action.name,
                "worker": self._worker_name,
                "language": "PYTHON",
                "frag_len": self._ws_max_reply_payload_size,
                "frag_count": frag_count,
                "reply_len": len(payload),
            },
        )

        return [
            StompFrame.SEND.build_frame(
                headers={
                    HeaderType.DESTINATION: f"/app/ml-worker/{self._worker_name}/reply",
                },
                body=FragmentedPayload(
                    id=data.id,
                    action=data.action.name,
                    payload=fragment_message(payload, frag_i, self._ws_max_reply_payload_size),
                    f_index=frag_i,
                    f_count=frag_count,
                ).json(by_alias=True),
            )
            for frag_i in range(frag_count)
        ]

    async def setup(self, websocket: WebSocketClientProtocol):
        LOGGER.info("Subscribing for action...")
        await self.subscribe(
            websocket,
            f"/ml-worker/{self._worker_name}/action",
            f"ws-worker-{self._worker_name}-action",
            self.action_handler,
        )
        LOGGER.info("Subscribing for config...")
        await self.subscribe(
            websocket,
            f"/ml-worker/{self._worker_name}/config",
            f"ws-worker-{self._worker_name}-config",
            self.config_handler,
        )

    async def start(
        self,
        restart: bool = False,
        nb_workers: Optional[int] = None,
    ):
        load_plugins()
        start_pool(nb_workers)
        await super().start(restart=restart)

    def stop(self):
        super().stop()
        shutdown_pool()
