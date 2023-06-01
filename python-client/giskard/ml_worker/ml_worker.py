import asyncio
import logging

import grpc
from grpc.aio._server import Server
from pydantic import AnyHttpUrl

from giskard import cli_utils
from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.bridge.ml_worker_bridge import MLWorkerBridge
from giskard.ml_worker.testing.registry.registry import load_plugins
from giskard.ml_worker.utils.error_interceptor import ErrorInterceptor
from giskard.settings import settings

logger = logging.getLogger(__name__)


class MLWorker:
    socket_file_location: str
    tunnel: MLWorkerBridge = None
    grpc_server: Server

    def __init__(self, is_server=False, backend_url: AnyHttpUrl = None, api_key=None) -> None:
        client = None if is_server else GiskardClient(backend_url, api_key)

        server, address = self._create_grpc_server(client, is_server)
        if not is_server:
            logger.info(
                "Remote server host and port are specified, connecting as an external ML Worker"
            )
            self.tunnel = MLWorkerBridge(address, client)

        self.grpc_server = server

    def _create_grpc_server(self, client: GiskardClient, is_server=False):
        from giskard.ml_worker.generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server
        from giskard.ml_worker.server.ml_worker_service import MLWorkerServiceImpl
        from giskard.ml_worker.utils.network import find_free_port

        server = grpc.aio.server(
            interceptors=[ErrorInterceptor()],
            options=[
                ("grpc.max_send_message_length", settings.max_send_message_length_mb * 1024 ** 2),
                ("grpc.max_receive_message_length", settings.max_receive_message_length_mb * 1024 ** 2),
            ]
        )

        if is_server:
            port = settings.port if settings.port else find_free_port()
            address = f"{settings.host}:{port}"
        else:
            worker_id = cli_utils.ml_worker_id(is_server, client.host_url)
            self.socket_file_location = f"{settings.home_dir / 'run' / f'ml-worker-{worker_id}.sock'}"
            address = f"unix://{self.socket_file_location}"

        add_MLWorkerServicer_to_server(MLWorkerServiceImpl(client, address, not is_server), server)
        server.add_insecure_port(address)
        logger.info(f"Started ML Worker server on {address}")
        logger.debug(f"ML Worker settings: {settings}")
        return server, address

    async def start(self):
        load_plugins()
        await self.grpc_server.start()
        if self.tunnel:
            await self.tunnel.start()
        await self.grpc_server.wait_for_termination()

        for t in asyncio.all_tasks():
            if t != asyncio.current_task():
                await t

    async def stop(self):
        await self.grpc_server.stop(5)
        if self.tunnel:
            self.tunnel.stop()
