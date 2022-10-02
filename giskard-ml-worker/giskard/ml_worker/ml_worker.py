import asyncio
import logging

import grpc

from giskard.settings import settings

logger = logging.getLogger(__name__)


async def _start_grpc_server(remote=False):
    from giskard.ml_worker.generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server
    from giskard.ml_worker.server.ml_worker_service import MLWorkerServiceImpl
    from giskard.ml_worker.utils.network import find_free_port

    server = grpc.aio.server(
        # interceptors=[ErrorInterceptor()],
        options=[
            ('grpc.max_send_message_length', settings.max_send_message_length_mb * 1024 ** 2),
            ('grpc.max_receive_message_length', settings.max_receive_message_length_mb * 1024 ** 2),
        ]
    )

    port = settings.port or find_free_port()
    add_MLWorkerServicer_to_server(MLWorkerServiceImpl(port, remote), server)
    server.add_insecure_port(f'{settings.host}:{port}')
    await server.start()
    logger.info(f"Started ML Worker server on port {port}")
    logger.debug(f"ML Worker settings: {settings}")
    return server, port


async def start_ml_worker(remote_host=None, remote_port=None):
    from giskard.ml_worker.bridge.ml_worker_bridge import MLWorkerBridge

    is_remote = remote_host is not None and remote_port is not None
    tasks = []
    server, grpc_server_port = await _start_grpc_server(is_remote)
    if is_remote:
        logger.info("Remote server host and port are specified, connecting as an external ML Worker")
        tunnel = MLWorkerBridge(grpc_server_port, remote_host, remote_port)
        tasks.append(asyncio.create_task(tunnel.start()))

    tasks.append(asyncio.create_task(server.wait_for_termination()))
    await asyncio.wait(tasks)
