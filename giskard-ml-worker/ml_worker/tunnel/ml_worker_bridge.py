import asyncio
import logging
import socket

from tenacity import retry, wait_exponential

from ml_worker.tunnel.error import ConnectionLost
from ml_worker.utils.logging import load_logging_config

START_INNER_SERVER = 0

CREATE_CLIENT_CHANNEL = 1

load_logging_config('')
logger = logging.getLogger()

grpc_sockets = {}
client_sockets = {}
client_to_grpc_task = {}
grpc_to_client_task = {}


class MLWorkerTunnel:
    def __init__(self, local_port: int, remote_host: str, remote_port: int,
                 execution_loop=asyncio.get_event_loop()) -> None:
        self.loop = execution_loop
        self.local_host = 'localhost'
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.buffers = {}
        self.buffer = b''

        self.remote_service_socket = None

    async def send_service_message(self, sock: socket.socket, msg_type: int, data: bytes = b''):
        msg_type_bytes = int.to_bytes(msg_type, 1, "big")
        message_len = len(msg_type_bytes) + len(data)
        await self.send(sock, message_len.to_bytes(4, "big") + msg_type_bytes + data)

    @retry(wait=wait_exponential(min=0.1, max=5, multiplier=0.1))
    async def start(self):
        try:
            self.remote_service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await self.loop.sock_connect(self.remote_service_socket, (self.remote_host, self.remote_port))
        except ConnectionRefusedError as e:
            logger.error(f"Failed to connect to a remote host: {self.remote_host}:{self.remote_port} : {str(e)}")
            raise e
        logger.info(f"Connected service socket to remote host {self.remote_host}:{self.remote_port}")
        await self.send_service_message(self.remote_service_socket, START_INNER_SERVER)

        self.loop.create_task(self.listen_remote_server_service_socket())

    async def send(self, sock, data):
        try:
            # peer_host, peer_port = sock.getpeername()
            # logger.debug(f"Sending {len(data)} bytes to {peer_host}:{peer_port}")
            await self.loop.sock_sendall(sock, data)
        except Exception as e:
            print(e)

    async def recv(self, sock: socket.socket, size=1024 * 256):
        try:
            # peer_host, peer_port = sock.getpeername()
            sock.setblocking(False)
            data = await self.loop.sock_recv(sock, size)
            is_grpc_socket = sock in grpc_sockets.values()
            # logger.debug(f"Read {len(data)} bytes from {peer_host}:{peer_port}" + (" (grpc)" if is_grpc_socket else ""))

            if not len(data):
                if not self.is_connected(sock):
                    s: socket.socket
                    for c, s in grpc_sockets.items():
                        if s == sock:
                            logger.info(f"Removing disconnected client {c}")
                            s.close()
                sock.close()
                # logger.warning(f"Connection to {peer_host}:{peer_port} lost")
                raise ConnectionLost()

            return data
        except Exception as e:
            raise e

    async def listen_remote_server_service_socket(self):
        logger.info("Created remote server listener task")
        while True:
            try:
                data = await self.recv(self.remote_service_socket)
                client = data[:8]
                command = int.from_bytes(data[8:], "big")
                await self.handle_server_command(client, command)
            except ConnectionLost:
                await self.start()

    async def handle_server_command(self, client, command):
        if command == CREATE_CLIENT_CHANNEL:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.remote_host, self.remote_port))
            logger.info(f"Connected client {client} to remote host {(self.remote_host, self.remote_port)}")
            await self.send_service_message(client_socket, CREATE_CLIENT_CHANNEL, client)
            client_sockets[client] = client_socket

            grpc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            grpc_socket.connect((self.local_host, self.local_port))
            grpc_sockets[client] = grpc_socket
            logger.info(f"Connected client {client} to grpc host {(self.local_host, self.local_port)}")

            self.loop.create_task(self.grpc_to_client(grpc_socket, client_socket))
            self.loop.create_task(self.client_to_grpc(grpc_socket, client_socket))

    async def client_to_grpc(self, grpc_socket, client_socket):
        logger.info("Created remote->grpc sync task")
        try:
            while True:
                data = None
                data = await self.recv(client_socket)
                await self.send(grpc_socket, data)
        except ConnectionLost as e:
            logger.exception(e)
            print(1)
            client_socket.close()
            grpc_socket.close()
            # grpc_sockets.pop(client).close()
            # client_sockets.pop(client).close()
        except Exception as e:
            logger.exception(e)
            # client_to_grpc_task.pop(client).cancel()
            # grpc_to_client_task.pop(client).cancel()

    async def grpc_to_client(self, grpc_socket, client_socket):
        logger.info("Created grpc->remote sync task")
        try:
            while True:
                # sock = grpc_sockets[client]
                data = await self.recv(grpc_socket)
                await self.send(client_socket, data)
        except ConnectionLost:
            print(1)
            # client_sockets.pop(client).close()
            # grpc_sockets.pop(client).close()
            # client_to_grpc_task.pop(client).cancel()
            # grpc_to_client_task.pop(client).cancel()
        except Exception as e:
            print(e)

    @staticmethod
    def is_connected(s: socket.socket):
        try:
            return s.getpeername() is not None
        except:
            return False
