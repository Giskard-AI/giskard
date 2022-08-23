import asyncio
import logging
import socket

from ml_worker.utils.logging import load_logging_config

load_logging_config('')
logger = logging.getLogger()

connected_clients = {}

with_headers = False


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

        self.remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    async def start(self):
        self.remote_socket.connect((self.remote_host, self.remote_port))
        logger.info(f"Connected to remote host {(self.remote_host, self.remote_port)}")

        self.loop.create_task(self.remote_to_grpc())

    async def connect_and_handshake(self, client, initial_data):
        grpc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected_clients[client] = grpc_socket
        grpc_socket.connect((self.local_host, self.local_port))
        logger.info(f"Connected to local host {(self.local_host, self.local_port)}")

        grpc_handshake, _ = await self.recv(grpc_socket)
        await self.send_to_remote(client, grpc_handshake)

        # await self.send(grpc_socket, initial_data)

        logger.info("Finished handshake")

        self.loop.create_task(self.grpc_to_remote(client, grpc_socket))

    async def send(self, sock, data):
        # sock.setblocking(False)
        logger.info(f"Sending {len(data)} bytes to {sock.getpeername()}")
        await self.loop.sock_sendall(sock, data)
        logger.info(f"Sent {len(data)} bytes to {sock.getpeername()}")

    async def recv(self, sock: socket.socket, size=1024 * 256):
        data = None
        sock.setblocking(False)
        logger.info(f"Reading from {sock.getpeername()}")
        data = await self.loop.sock_recv(sock, size)
        logger.info(f"Read {len(data)} bytes from {sock.getpeername()}")

        if not len(data):
            if not self.is_connected(sock):
                s: socket.socket
                for c, s in connected_clients.items():
                    if s == sock:
                        logger.info(f"Removing disconnected client {c}")
                        s.close()
            logger.error("Connection lost")
            raise Exception("Connection lost")
        if self.remote_socket == sock:
            if with_headers:
                self.buffer += data
                client = self.buffer[:8]
                length = int.from_bytes(self.buffer[8:12], "big")
                payload = self.buffer[12:12 + length]
                self.buffer = self.buffer[12 + length:]
                return payload, client
            else:
                return data, None
        else:
            return data, None

    async def send_to_remote(self, client: bytes, data: bytes):
        if with_headers:
            logger.info(f"Send to remote: {client.decode()}-{len(data)}")
            await self.send(self.remote_socket, client + len(data).to_bytes(4, "big") + data)
        else:
            await self.send(self.remote_socket, data)

    async def remote_to_grpc(self):
        logger.info("Created remote->grpc sync task")
        while True:
            try:
                data, client = await self.recv(self.remote_socket)
                if client not in connected_clients:
                    await self.connect_and_handshake(client, data)
                grpc_socket = connected_clients.get(client)
                await self.send(grpc_socket, data)
            except Exception as e:
                print(e)

    async def grpc_to_remote(self, client, grpc_socket):
        logger.info("Created grpc->remote sync task")
        while True:
            try:
                data, _ = await self.recv(grpc_socket)
                await self.send_to_remote(client, data)
            except Exception as e:
                print(e)

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
