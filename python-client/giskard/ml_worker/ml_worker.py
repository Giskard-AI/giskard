import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import grpc
from pydantic import AnyHttpUrl

from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.testing.registry.registry import load_plugins
from giskard.ml_worker.utils.error_interceptor import ErrorInterceptor
from giskard.settings import settings

logger = logging.getLogger(__name__)


async def _start_grpc_server(client: GiskardClient, is_server=False):
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

    port = settings.port if settings.port and is_server else find_free_port()
    add_MLWorkerServicer_to_server(MLWorkerServiceImpl(client, port, not is_server), server)
    server.add_insecure_port(f"{settings.host}:{port}")
    await server.start()
    logger.info(f"Started ML Worker server on port {port}")
    logger.debug(f"ML Worker settings: {settings}")
    return server, port


async def start_ml_worker(is_server=False, backend_url: AnyHttpUrl = None, api_key=None):
    load_plugins()
    from giskard.ml_worker.bridge.ml_worker_bridge import MLWorkerBridge

    tasks = []

    client = GiskardClient(backend_url, api_key) if api_key != 'INTERNAL_ML_WORKER' else None

    server, grpc_server_port = await _start_grpc_server(client, is_server)
    if not is_server:
        logger.info(
            "Remote server host and port are specified, connecting as an external ML Worker"
        )

        tunnel = MLWorkerBridge(grpc_server_port, client)
        tasks.append(asyncio.create_task(tunnel.start()))

    tasks.append(asyncio.create_task(server.wait_for_termination()))
    await asyncio.wait(tasks)
