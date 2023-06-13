import asyncio
import base64
import logging
import sys
from asyncio import StreamReader, StreamWriter, IncompleteReadError
from os import environ
from random import random
from tenacity import retry, wait_exponential, stop_after_attempt, after_log
from typing import Optional
from urllib.parse import urlparse

from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.bridge.data_encryptor import DataEncryptor
from giskard.ml_worker.bridge.error import ConnectionLost
from giskard.ml_worker.bridge.service_messages import CREATE_CLIENT_CHANNEL, START_INNER_SERVER
from giskard.ml_worker.utils.network import readable_hex
from giskard.utils.analytics_collector import anonymize, analytics

CHANNEL_ID_LENGTH = 8

logger = logging.getLogger(__name__)

# Some python versions (3.10 for examples) may garbage collect readers that are in use
# it leads to GeneratorExit errors in coroutines and failed GRPC calls
# this set is meant to keep readers references so that GC doesn't collect them
readers = set()
writers = set()


class MLWorkerBridge:
    key_id: str
    encryptor: DataEncryptor
    remote_host: str
    remote_port: int

    def __init__(
        self,
        local_address: str,
        client: GiskardClient,
    ) -> None:
        self.stopping = False
        self.local_address = local_address

        self.client = client

        self.service_channel_reader: Optional[StreamReader] = None
        self.service_channel_writer: Optional[StreamWriter] = None

    async def stop(self):
        logger.info(f"Stopping the bridge with {self.local_address}")
        self.stopping = True
        await self.close_service_channel()
        for w in writers:
            w.close()

    @retry(wait=wait_exponential(min=0.1, max=5, multiplier=0.1))
    async def start(self):
        try:
            await self.connect_to_remote_host()
            await self.send_start_inner_server_message()
            await self.listen_remote_server_service_socket()

        except Exception as e:
            await self.close_service_channel()
            logger.error(f"Failed to connect to a remote host: {self.remote_host}:{self.remote_port} : {str(e)}")
            analytics.track(
                "Start ML Worker Bridge error",
                {"host": anonymize(self.remote_host), "port": anonymize(self.remote_port), "error": str(e)},
                force=True,
            )
            raise e

    async def close_service_channel(self):
        if self.service_channel_writer:
            self.service_channel_writer.close()
            await self.service_channel_writer.wait_closed()
            writers.remove(self.service_channel_writer)
        if self.service_channel_reader:
            readers.remove(self.service_channel_reader)

    def fetch_connection_details(self):
        info = self.client.get_server_info()
        self.remote_host = (
            environ.get("GSK_EXTERNAL_ML_WORKER_HOST")
            or info.get("externalMlWorkerEntrypointHost")
            or urlparse(self.client.host_url).hostname
        )

        self.remote_port = (
            environ.get("GSK_EXTERNAL_ML_WORKER_PORT") or info.get("externalMlWorkerEntrypointPort") or 40051
        )

        encryption_key = base64.b64decode(info["encryptionKey"])

        self.key_id = info["keyId"]
        self.encryptor = DataEncryptor(encryption_key)

    async def connect_to_remote_host(self):
        self.fetch_connection_details()

        logger.info(f"Connecting to {self.remote_host}:{self.remote_port}")
        self.service_channel_reader, self.service_channel_writer = await asyncio.open_connection(
            self.remote_host, self.remote_port
        )
        readers.add(self.service_channel_reader)
        writers.add(self.service_channel_writer)
        logger.info(f"Connected to Giskard server {self.remote_host}:{self.remote_port}")

    async def send_start_inner_server_message(self):
        self.service_channel_writer.write(
            self.encryptor.encrypt(START_INNER_SERVER, additional_data=self.key_id.encode())
        )
        await self.service_channel_writer.drain()

    async def listen_remote_server_service_socket(self):
        try:
            logger.debug("Created remote server listener task")
            while True:
                logger.debug("waiting for a service command")
                length = int.from_bytes(await self.service_channel_reader.readexactly(4), "big")
                encrypted_data = await self.service_channel_reader.readexactly(length)
                if len(encrypted_data):
                    data = self.encryptor.decrypt(encrypted_data)
                    client = data[:CHANNEL_ID_LENGTH]
                    command = data[CHANNEL_ID_LENGTH:]
                    logger.debug(f"service command received: {client}: {command}")
                    await self.handle_server_command(client, command)
                else:
                    raise ConnectionLost()
        except (IncompleteReadError, ConnectionLost, ConnectionResetError) as e:
            if self.stopping:
                return
            logger.info("Lost connection to Giskard server, retrying...")
            await self.stop()
            await asyncio.sleep(1 + random() * 2)
            await self.start()
            if isinstance(e, IncompleteReadError) and not self.stopping:
                logger.exception(e)
        except BaseException as e:  # NOSONAR
            logger.exception(e)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        after=after_log(logger, logging.WARNING),
    )
    async def handle_server_command(self, client, command):
        if command == CREATE_CLIENT_CHANNEL:
            remote_reader, remote_writer = await asyncio.open_connection(self.remote_host, self.remote_port)
            readers.add(remote_reader)
            writers.add(remote_writer)
            logger.debug(f"Connected client {client} to remote host {(self.remote_host, self.remote_port)}")
            message = CREATE_CLIENT_CHANNEL + client
            logger.debug(f"handle_server_command: Writing {len(message)} bytes: {readable_hex(message)}")
            remote_writer.write(self.encryptor.encrypt(message, additional_data=self.key_id.encode()))
            await remote_writer.drain()

            # On Windows, we go over TCP because UDS are not supported yet.
            # Check on gRPC every once in a while for eventual support.
            if sys.platform == "win32":
                address_parts = self.local_address.split(":")
                grpc_reader, grpc_writer = await asyncio.open_connection(address_parts[0], address_parts[1])
            # On Linux, we can use Unix Domain Sockets.
            else:
                grpc_reader, grpc_writer = await asyncio.open_unix_connection(urlparse(self.local_address).path)

            readers.add(grpc_reader)
            writers.add(grpc_writer)
            logger.debug(f"Connected client {client} to grpc host {self.local_address}")

            await self.create_sync_task(
                client, grpc_reader, remote_writer, encrypted_writer=True, task_name=f"{client.decode()}: grpc->remote"
            )
            await self.create_sync_task(
                client, remote_reader, grpc_writer, encrypted_reader=True, task_name=f"{client.decode()}: remote->grpc"
            )

    async def create_sync_task(
        self, client, reader, writer, encrypted_writer=False, encrypted_reader=False, task_name=""
    ):
        task = self.sync_data(client, reader, writer, encrypted_writer, encrypted_reader, task_name)
        if sys.version_info >= (3, 8):
            asyncio.create_task(task, name=task_name)
        else:
            asyncio.create_task(task)

    async def sync_data(
        self,
        client,
        reader: StreamReader,
        writer: StreamWriter,
        encrypted_writer=False,
        encrypted_reader=False,
        task_name: str = None,
    ):
        log_prefix = "" if not task_name else task_name + ": "
        try:
            while not reader.at_eof():
                if encrypted_reader:
                    length = await reader.readexactly(4)
                    data = await reader.readexactly(int.from_bytes(length, "big"))
                    if len(data):
                        data = self.encryptor.decrypt(data)
                else:
                    data = await reader.read(2048)
                if len(data):
                    logger.debug(f"{log_prefix}Writing {len(data)} bytes: {readable_hex(data)}")
                    if encrypted_writer:
                        data = self.encryptor.encrypt(data)
                    writer.write(data)
                    await writer.drain()
                else:
                    logger.debug(f"{log_prefix}Connection lost: {client}")
                    break
        except (IncompleteReadError, ConnectionLost, ConnectionResetError):
            logger.debug(f"{log_prefix}Connection lost: {client}")
        except BaseException:  # noqa
            logger.exception(f"{log_prefix}Sync data error")
        finally:
            writer.close()
            readers.remove(reader)
            writers.remove(writer)
