import asyncio
import logging

import grpc

from generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server
from ml_worker.server.ml_worker_service import MLWorkerServiceImpl
from ml_worker.tunnel.ml_worker_bridge import MLWorkerTunnel
from ml_worker.utils.logging import load_logging_config
from ml_worker.utils.network import find_free_port
from settings import Settings

settings = Settings()

load_logging_config()
logger = logging.getLogger()


async def start_grpc_server():
    logger.info("Starting local ML Worker server")
    server = grpc.aio.server(
        # interceptors=[ErrorInterceptor()],
        options=[
            ('grpc.max_send_message_length', settings.max_send_message_length_mb * 1024 ** 2),
            ('grpc.max_receive_message_length', settings.max_receive_message_length_mb * 1024 ** 2),
        ]
    )

    add_MLWorkerServicer_to_server(MLWorkerServiceImpl(), server)
    port = settings.port or find_free_port()
    server.add_insecure_port(f'{settings.host}:{port}')
    await server.start()
    logging.info(f"Started ML Worker server on port {port} with settings [{settings}]")
    return server, port


async def start():
    tasks = []
    server, grpc_server_port = await start_grpc_server()
    remote_host = 'localhost'
    remote_port = 10050
    tunnel = MLWorkerTunnel(grpc_server_port, remote_host, remote_port)

    tasks.append(asyncio.create_task(tunnel.start()))
    tasks.append(asyncio.create_task(server.wait_for_termination()))
    await asyncio.wait(tasks)


if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(start())
    except KeyboardInterrupt:
        logger.info("Exiting")
