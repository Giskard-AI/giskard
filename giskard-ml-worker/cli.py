import asyncio
import logging

import click
import grpc
from click import STRING, INT

from ml_worker.utils.logging import load_logging_config
from settings import Settings

settings = Settings()

load_logging_config()
logger = logging.getLogger()


async def start_grpc_server(remote=False):
    from generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server
    from ml_worker.server.ml_worker_service import MLWorkerServiceImpl
    from ml_worker.utils.network import find_free_port
    from settings import Settings
    settings = Settings()
    logger.info("Starting local ML Worker server")
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
    logging.info(f"Started ML Worker server on port {port}")
    logging.debug(f"ML Worker settings: {settings}")
    return server, port


async def start(remote_host=None, remote_port=None):
    from ml_worker.bridge.ml_worker_bridge import MLWorkerBridge

    is_remote = remote_host is not None and remote_port is not None
    tasks = []
    server, grpc_server_port = await start_grpc_server(is_remote)
    if is_remote:
        logger.info("Remote server host and port are specified, connecting as an external ML Worker")
        tunnel = MLWorkerBridge(grpc_server_port, remote_host, remote_port)
        tasks.append(asyncio.create_task(tunnel.start()))

    tasks.append(asyncio.create_task(server.wait_for_termination()))
    await asyncio.wait(tasks)


@click.command(help="Start ML Worker", context_settings={'show_default': True})
@click.option('--host', '-h', type=STRING, help='Remote Giskard host address to connect to')
@click.option('--port', '-p', type=INT, default=40051,
              help='Remote Giskard port accepting external ML Worker connections')
def cli(host, port):
    try:
        asyncio.get_event_loop().run_until_complete(start(host, port))
    except KeyboardInterrupt:
        logger.info("Exiting")


if __name__ == '__main__':
    cli()
