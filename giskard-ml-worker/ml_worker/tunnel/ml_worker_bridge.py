import asyncio
import logging
import socket

from ml_worker.utils.logging import load_logging_config

START_INNER_SERVER = 0

CREATE_CLIENT_CHANNEL = 1

load_logging_config('')
logger = logging.getLogger()

grpc_sockets = {}
client_sockets = {}


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

        self.remote_main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    async def send_service_message(self, sock: socket.socket, msg_type: int, data: bytes = b''):
        msg_type_bytes = int.to_bytes(msg_type, 1, "big")
        message_len = len(msg_type_bytes) + len(data)
        await self.send(sock, message_len.to_bytes(4, "big") + msg_type_bytes + data)

    async def start(self):
        self.remote_main_socket.connect((self.remote_host, self.remote_port))
        # self.remote_main_socket.setblocking(False)
        # logger.info(f"Connected remote main socket to {(self.remote_host, self.remote_port)}")
        await self.send_service_message(self.remote_main_socket, START_INNER_SERVER)

        self.loop.create_task(self.listen_remote_server_socket())

    async def connect_to_grpc_and_handshake(self, client):
        grpc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        grpc_socket.connect((self.local_host, self.local_port))
        # grpc_socket.setblocking(False)
        grpc_sockets[client] = grpc_socket
        # logger.info(f"Connected client {client} to local host {(self.local_host, self.local_port)}")

        grpc_handshake = await self.recv(grpc_socket)
        await self.send(client_sockets[client], grpc_handshake)

        # logger.info("Finished handshake")

    async def send(self, sock, data):
        # logger.info(f"Sending {len(data)} bytes to {sock.getpeername()}")
        await self.loop.sock_sendall(sock, data)
        # logger.info(f"Sent {len(data)} bytes to {sock.getpeername()}")

    async def recv(self, sock: socket.socket, size=1024 * 256):
        # logger.info(f"Reading from {sock.getpeername()}")
        sock.setblocking(False)
        data = await self.loop.sock_recv(sock, size)
        # logger.info(f"Read {len(data)} bytes from {sock.getpeername()}")

        if not len(data):
            if not self.is_connected(sock):
                s: socket.socket
                for c, s in grpc_sockets.items():
                    if s == sock:
                        # logger.info(f"Removing disconnected client {c}")
                        s.close()
            logger.error("Connection lost")
            sock.close()

        return data

    async def listen_remote_server_socket(self):
        # logger.info("Created remote server listener task")
        while True:
            data = await self.recv(self.remote_main_socket)
            client = data[:8]
            command = int.from_bytes(data[8:], "big")
            await self.handle_server_command(client, command)

    async def handle_server_command(self, client, command):
        if command == CREATE_CLIENT_CHANNEL:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.remote_host, self.remote_port))
            # client_socket.setblocking(False)
            # logger.info(f"Connected client {client} to remote host {(self.remote_host, self.remote_port)}")
            await self.send_service_message(client_socket, CREATE_CLIENT_CHANNEL, client)
            client_sockets[client] = client_socket

            await self.connect_to_grpc_and_handshake(client)

            self.loop.create_task(self.client_to_grpc(client))
            self.loop.create_task(self.grpc_to_client(client))

    async def client_to_grpc(self, client):
        # logger.info("Created remote->grpc sync task")
        while True:
            data = await self.recv(client_sockets[client])
            await self.send(grpc_sockets[client], data)
        print(1)

    async def grpc_to_client(self, client):
        # logger.info("Created grpc->remote sync task")
        while True:
            data = await self.recv(grpc_sockets[client])
            await self.send(client_sockets[client], data)
        print(1)

    @staticmethod
    def is_connected(s: socket.socket):
        try:
            return s.getpeername() is not None
        except:
            return False


loop = asyncio.get_event_loop()
tunnel = MLWorkerTunnel(50051, 'localhost', 10050)
loop.create_task(tunnel.start())
loop.run_forever()
