import asyncio
import logging
from asyncio import StreamReader, StreamWriter

from tenacity import retry, wait_exponential

from giskard.ml_worker.bridge.error import ConnectionLost
from giskard.ml_worker.bridge.service_messages import START_INNER_SERVER, CREATE_CLIENT_CHANNEL
from giskard.ml_worker.utils.network import readable_hex

logger = logging.getLogger(__name__)


class MLWorkerBridge:
    def __init__(self, local_port: int, remote_host: str, remote_port: int,
                 execution_loop=asyncio.get_event_loop()) -> None:
        self.loop = execution_loop

        self.local_host = 'localhost'
        self.local_port = local_port

        self.remote_host = remote_host
        self.remote_port = remote_port

    @retry(wait=wait_exponential(min=0.1, max=5, multiplier=0.1))
    async def start(self):
        remote_writer = None
        try:
            logger.info(f"Connecting to {self.remote_host}:{self.remote_port}")
            remote_reader, remote_writer = await asyncio.open_connection(self.remote_host, self.remote_port)
            logger.info(f"Connected to Giskard server {self.remote_host}:{self.remote_port}")
            await self.send_service_message(remote_writer, START_INNER_SERVER)
            self.loop.create_task(self.listen_remote_server_service_socket(remote_reader))
        except Exception as e:
            remote_writer.close()
            await remote_writer.wait_closed()
            logger.error(f"Failed to connect to a remote host: {self.remote_host}:{self.remote_port} : {str(e)}")
            raise e

    async def send_service_message(self, remote_writer: StreamWriter, msg_type: int, data: bytes = b''):
        msg = self.create_service_message(msg_type, data)
        logger.debug(f"Service message: Writing {len(msg)} bytes: {readable_hex(msg)}")
        remote_writer.write(msg)
        await remote_writer.drain()

    @staticmethod
    def create_service_message(msg_type: int, data: bytes = b''):
        msg_type_bytes = int.to_bytes(msg_type, 1, "big")
        message_len = len(msg_type_bytes) + len(data)
        msg = message_len.to_bytes(4, "big") + msg_type_bytes + data
        return msg

    async def listen_remote_server_service_socket(self, remote_reader: StreamReader):
        try:
            logger.debug("Created remote server listener task")
            while True:
                logger.debug("waiting for a service command")
                data = await remote_reader.read(9)  # command payload is 1 byte by design
                if len(data):
                    client = data[:8]
                    command = int.from_bytes(data[8:], "big")
                    logger.debug(f"service command received: {client}: {command}")
                    await self.handle_server_command(client, command)
                else:
                    raise ConnectionLost()
        except ConnectionLost:
            logger.info("Connection to Giskard host lost")
            await self.start()
        except Exception as e:
            logger.exception(e)

    async def handle_server_command(self, client, command):
        if command == CREATE_CLIENT_CHANNEL:
            remote_reader, remote_writer = await asyncio.open_connection(self.remote_host, self.remote_port)
            logger.debug(f"Connected client {client} to remote host {(self.remote_host, self.remote_port)}")
            message = self.create_service_message(CREATE_CLIENT_CHANNEL, client)
            logger.debug(f"handle_server_command: Writing {len(message)} bytes: {readable_hex(message)}")
            remote_writer.write(message)
            await remote_writer.drain()

            grpc_reader, grpc_writer = await asyncio.open_connection(self.local_host, self.local_port)
            logger.debug(f"Connected client {client} to grpc host {(self.local_host, self.local_port)}")

            self.loop.create_task(
                self.sync_data(client, grpc_reader, remote_writer, f"{client.decode()}: grpc->remote"))
            self.loop.create_task(
                self.sync_data(client, remote_reader, grpc_writer, f"{client.decode()}: remote->grpc"))

    @staticmethod
    async def sync_data(client, reader: StreamReader, writer: StreamWriter, task_name: str = None):
        log_prefix = '' if not task_name else task_name + ': '
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
        except (ConnectionLost, ConnectionResetError):
            logger.debug(f"{log_prefix}Connection lost: {client}")
        except Exception:
            logger.exception(f"{log_prefix}Sync data error")
