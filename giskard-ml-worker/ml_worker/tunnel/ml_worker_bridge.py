import asyncio
import logging
import socket

from ml_worker.utils.logging import load_logging_config

load_logging_config()
logger = logging.getLogger()


class MLWorkerTunnel:
    def __init__(self, local_port: int, remote_host: str, remote_port: int,
                 execution_loop=asyncio.get_event_loop()) -> None:
        self.loop = execution_loop
        self.local_host = 'localhost'
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.grpc_socket = socket.socket()
        self.remote_socket = socket.socket()

    async def start(self):
        await self.connect_and_handshake()

        self.loop.create_task(self.sync_sockets(self.grpc_socket, self.remote_socket, name='grpc->remote'))
        logger.info("Created grpc->remote task")

        self.loop.create_task(self.sync_sockets(self.remote_socket, self.grpc_socket, name='remote->grpc'))
        logger.info("Created remote->grpc task")

    async def connect_and_handshake(self):
        self.remote_socket.connect((self.remote_host, self.remote_port))
        logger.info(f"Connected to remote host {(self.remote_host, self.remote_port)}")

        initial_data = await self.recv(self.remote_socket)

        self.grpc_socket.connect((self.local_host, self.local_port))
        logger.info(f"Connected to local host {(self.local_host, self.local_port)}")

        grpc_handshake = await self.recv(self.grpc_socket)

        await self.loop.sock_sendall(self.remote_socket, grpc_handshake)
        logger.info(f"grpc->remote: Sending {len(grpc_handshake)} bytes from {self.grpc_socket.getpeername()} to {self.remote_socket.getpeername()}")

        await self.loop.sock_sendall(self.grpc_socket, initial_data)
        logger.info(f"remote->grpc: Sending {len(initial_data)} bytes from {self.remote_socket.getpeername()} to {self.grpc_socket.getpeername()}")

        logger.info("Finished handshake")

    async def recv(self, sock, size=1024 * 256):
        data = await self.loop.sock_recv(sock, size)
        if not len(data):
            raise Exception("Connection lost")
        if self.remote_socket == sock:
            client = data[:8]
            data = data[8:]
        return data

    async def sync_sockets(self, read_from, write_to, name=None):
        read_from.setblocking(False)
        write_to.setblocking(False)
        while True:
            data = await self.recv(read_from)
            logger.info(f"{name}: Sending {len(data)} bytes from {read_from.getpeername()} to {write_to.getpeername()}")
            await self.loop.sock_sendall(write_to, data)

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
#
# async def foo():
#     await asyncio.sleep(3)
#     print('foo')
#
# async def bar():
#     await asyncio.sleep(5)
#     print('bar')
#
#
# async def main():
#     loop.create_task(foo())
#     loop.create_task(bar())
#
# loop.create_task(main())
# loop.run_forever()
#
