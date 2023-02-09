import asyncio
import collections
import hashlib
import logging
import os
import sys
from time import sleep

from daemon import DaemonContext
from daemon.daemon import change_working_directory
from daemon.runner import is_pidfile_stale
from lockfile.pidlockfile import PIDLockFile

from giskard.ml_worker.ml_worker import start_ml_worker
from giskard.path_utils import run_dir
from giskard.settings import settings

logger = logging.getLogger(__name__)


def remove_stale_pid_file(pid_file):
    if is_pidfile_stale(pid_file):
        logger.debug("Stale PID file found, removing it")
        pid_file.break_lock()


def create_pid_file_path(is_server, host, port):
    key = f"{sys.executable}"
    if not is_server:
        key += f"{host}{port}"
    hash_value = hashlib.sha1(key.encode()).hexdigest()
    return run_dir / f"ml-worker-{hash_value}.pid"


def run_daemon(is_server, host, port):
    log_path = get_log_path()
    logger.info(f"Writing logs to {log_path}")
    pid_file = PIDLockFile(create_pid_file_path(is_server, host, port))

    with DaemonContext(pidfile=pid_file, stdout=open(log_path, "w+t")) as c:
        workdir = settings.home_dir / "tmp" / f"daemon-run-{os.getpid()}"
        workdir.mkdir(exist_ok=True, parents=True)
        change_working_directory(workdir)

        logger.info(f"Daemon PID: {os.getpid()}")
        asyncio.get_event_loop().run_until_complete(start_ml_worker(is_server, host, port))


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
