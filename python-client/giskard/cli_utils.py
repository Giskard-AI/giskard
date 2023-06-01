import asyncio
import collections
import hashlib
import logging
import os
import sys
from time import sleep

from daemon import DaemonContext
from daemon.runner import is_pidfile_stale
from lockfile.pidlockfile import PIDLockFile
from pydantic import AnyHttpUrl, parse_obj_as

from giskard.path_utils import run_dir

logger = logging.getLogger(__name__)


def remove_stale_pid_file(pid_file):
    if is_pidfile_stale(pid_file):
        logger.debug("Stale PID file found, removing it")
        pid_file.break_lock()


def create_pid_file_path(is_server, url):
    hash_value = ml_worker_id(is_server, url)
    return run_dir / f"ml-worker-{hash_value}.pid"


def ml_worker_id(is_server, url):
    key = f"{sys.executable}"
    if not is_server:
        key += url
    hash_value = hashlib.sha1(key.encode()).hexdigest()
    return hash_value


def validate_url(_ctx, _param, value) -> AnyHttpUrl:
    return parse_obj_as(AnyHttpUrl, value)


def run_daemon(is_server, url, api_key):
    from giskard.ml_worker.ml_worker import MLWorker

    log_path = get_log_path()
    logger.info(f"Writing logs to {log_path}")
    pid_file = PIDLockFile(create_pid_file_path(is_server, url))

    with DaemonContext(pidfile=pid_file, stdout=open(log_path, "w+t")):
        logger.info(f"Daemon PID: {os.getpid()}")
        asyncio.get_event_loop().run_until_complete(MLWorker(is_server, url, api_key).start())


def get_log_path():
    return run_dir / "ml-worker.log"


def tail(filename, n=100):
    """Return the last n lines of a file"""
    return collections.deque(open(filename), n)


def follow_file(filename):
    if not os.path.exists(filename):
        print(f"{filename} does not exists")
        return

    wait = 1
    with open(filename) as fp:
        exit_pooling = False
        skip_existing = True
        while not exit_pooling:
            line = fp.readline()

            if not line:
                skip_existing = False
                sleep(wait)
            elif not skip_existing:
                print(line, end="")
