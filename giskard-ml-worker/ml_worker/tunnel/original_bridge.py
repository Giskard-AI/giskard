import asyncio
import socket


def is_connected(s: socket.socket):
    try:
        return s.getpeername() is not None
    except:
        return False


async def recv(loop, socket, size=1024*256):
    data = await loop.sock_recv(socket, size)
    if not len(data):
        raise Exception("Connection lost")
    return data


grpc_socket = socket.socket()
# grpc_socket.connect(('localhost', 50051))  # to gRPC
remote_socket = socket.socket()
remote_socket.connect(('localhost', 10050))  # to remote


async def run_one(read_from, write_to, differed=False):
    loop = asyncio.get_event_loop()
    read_from.setblocking(False)
    while True:
        data = await recv(loop, read_from)
        if read_from == remote_socket:
            data = data[8:]
        await loop.sock_sendall(write_to, data)


async def start():
    loop = asyncio.get_event_loop()
    data = await recv(loop, remote_socket)
    data = data[8:]
    grpc_socket.connect(('localhost', 50051))
    grpc_handshake = await recv(loop, grpc_socket)
    await loop.sock_sendall(remote_socket, grpc_handshake)
    loop.create_task(run_one(read_from=grpc_socket, write_to=remote_socket))
    await loop.sock_sendall(grpc_socket, data)
    loop.create_task(run_one(remote_socket, grpc_socket))


async def read_remote_to_grpc():
    loop = asyncio.get_event_loop()
    while True:
        data = await recv(loop, remote_socket)
        if len(data):
            await loop.sock_sendall(grpc_socket, data)


loop = asyncio.get_event_loop()
loop.create_task(start())
loop.run_forever()
