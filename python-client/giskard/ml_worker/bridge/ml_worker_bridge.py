import asyncio
import logging
import sys
from asyncio import StreamReader, StreamWriter
from random import random

from tenacity import retry, wait_exponential

from giskard.cli import analytics
from giskard.client.analytics_collector import anonymize
from giskard.ml_worker.bridge.error import ConnectionLost
from giskard.ml_worker.bridge.service_messages import CREATE_CLIENT_CHANNEL, START_INNER_SERVER
from giskard.ml_worker.utils.network import readable_hex

logger = logging.getLogger(__name__)

# Some python versions (3.10 for examples) may garbage collect readers that are in use
# it leads to GeneratorExit errors in coroutines and failed GRPC calls
# this set is meant to keep readers references so that GC doesn't collect them
readers = set()


class MLWorkerBridge:
    def __init__(
            self,
            local_port: int,
            remote_host: str,
            remote_port: int,
            execution_loop=asyncio.get_event_loop(),
    ) -> None:
        self.loop = execution_loop

        self.local_host = "localhost"
        self.local_port = local_port

        self.remote_host = remote_host
        self.remote_port = remote_port

        self.service_channel_reader = None
        self.service_channel_writer = None

    @retry(wait=wait_exponential(min=0.1, max=5, multiplier=0.1))
    async def start(self):
        try:
            await self.connect_to_remote_host()

            await self.send_service_message(START_INNER_SERVER)
            self.loop.create_task(self.listen_remote_server_service_socket())
        except Exception as e:
            await self.close_service_channel()
            logger.error(f"Failed to connect to a remote host: {self.remote_host}:{self.remote_port} : {str(e)}")
            analytics.track("Start ML Worker Bridge error", {
                "host": anonymize(self.remote_host),
                "port": anonymize(self.remote_port),
                "error": str(e)
            }, force=True)
            raise e

    async def close_service_channel(self):
        if self.service_channel_writer:
            self.service_channel_writer.close()
            await self.service_channel_writer.wait_closed()
        if self.service_channel_reader:
            readers.remove(self.service_channel_reader)

    async def connect_to_remote_host(self):
        logger.info(f"Connecting to {self.remote_host}:{self.remote_port}")
        self.service_channel_reader, self.service_channel_writer = await asyncio.open_connection(
            self.remote_host, self.remote_port
        )
        readers.add(self.service_channel_reader)
        logger.info(f"Connected to Giskard server {self.remote_host}:{self.remote_port}")

    async def send_service_message(self, msg_type: int, data: bytes = b""):
        msg = self.create_service_message(msg_type, data)
        logger.debug(f"Service message: Writing {len(msg)} bytes: {readable_hex(msg)}")
        self.service_channel_writer.write(msg)
        await self.service_channel_writer.drain()

    @staticmethod
    def create_service_message(msg_type: int, data: bytes = b""):
        msg_type_bytes = int.to_bytes(msg_type, 1, "big")
        message_len = len(msg_type_bytes) + len(data)
        msg = message_len.to_bytes(4, "big") + msg_type_bytes + data
        return msg

    async def listen_remote_server_service_socket(self):
        try:
            try:
                logger.debug("Created remote server listener task")
                while True:
                    logger.debug("waiting for a service command")
                    data = await self.service_channel_reader.read(9)  # command payload is 1 byte by design
                    if len(data):
                        client = data[:8]
                        command = int.from_bytes(data[8:], "big")
                        logger.debug(f"service command received: {client}: {command}")
                        await self.handle_server_command(client, command)
                    else:
                        raise ConnectionLost()
            finally:
                await self.close_service_channel()
        except (ConnectionLost, ConnectionResetError):
            logger.info("Lost connection to Giskard server, retrying...")
            await asyncio.sleep(1 + random() * 2)
            await self.start()
        except BaseException as e:  # NOSONAR
            logger.exception(e)

    async def handle_server_command(self, client, command):
        if command == CREATE_CLIENT_CHANNEL:
            remote_reader, remote_writer = await asyncio.open_connection(
                self.remote_host, self.remote_port
            )
            readers.add(remote_reader)
            logger.debug(
                f"Connected client {client} to remote host {(self.remote_host, self.remote_port)}"
            )
            message = self.create_service_message(CREATE_CLIENT_CHANNEL, client)
            logger.debug(
                f"handle_server_command: Writing {len(message)} bytes: {readable_hex(message)}"
            )
            remote_writer.write(message)
            await remote_writer.drain()

            grpc_reader, grpc_writer = await asyncio.open_connection(
                self.local_host, self.local_port
            )
            readers.add(grpc_reader)
            logger.debug(f"Connected client {client} to grpc host {(self.local_host, self.local_port)}")

            await self.create_sync_task(client, grpc_reader, remote_writer, f"{client.decode()}: grpc->remote")
            await self.create_sync_task(client, remote_reader, grpc_writer, f"{client.decode()}: remote->grpc")

    async def create_sync_task(self, client, reader, writer, task_name=""):
        task = self.sync_data(client, reader, writer, task_name)
        if sys.version_info >= (3, 8):
            self.loop.create_task(task, name=task_name)
        else:
            self.loop.create_task(task)

    @staticmethod
    async def sync_data(client, reader: StreamReader, writer: StreamWriter, task_name: str = None):
        log_prefix = "" if not task_name else task_name + ": "
        try:
            try:
                while not reader.at_eof():
                    data = await reader.read(2048)
                    if len(data):
                        logger.debug(f"{log_prefix}Writing {len(data)} bytes: {readable_hex(data)}")
                        writer.write(data)
                        await writer.drain()
                    else:
                        raise ConnectionLost()
            finally:
                writer.close()
                readers.remove(reader)
        except (ConnectionLost, ConnectionResetError):
            logger.debug(f"{log_prefix}Connection lost: {client}")
        except BaseException:  # NOSONAR
            logger.exception(f"{log_prefix}Sync data error")
