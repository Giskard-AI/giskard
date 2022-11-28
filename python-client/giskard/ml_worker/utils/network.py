import codecs
import os
import socket
from contextlib import closing


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def readable_hex(data):
    if not os.environ.get("GSK_ML_WORKER_LOG_HEX", False):
        return ""
    s = codecs.encode(data, "hex").decode()
    return " ".join(s[i: i + 2] for i in range(0, len(s), 2))
