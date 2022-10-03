import asyncio
import hashlib
import logging
import os

import sys
from daemon import DaemonContext
from daemon.runner import is_pidfile_stale
from lockfile.pidlockfile import PIDLockFile

from giskard.ml_worker.ml_worker import start_ml_worker
from giskard.settings import run_dir

logger = logging.getLogger(__name__)


def remove_stale_pid_file(pid_file):
    if is_pidfile_stale(pid_file):
        logger.debug("Stale PID file found, removing it")
        pid_file.break_lock()


def create_pid_file_path(host, port):
    hash_value = hashlib.sha1(f"{host}{port}{sys.executable}".encode("UTF-8")).hexdigest()
    return run_dir / f"ml-worker-{hash_value}.pid"


def run_daemon(host, port):
    log_path = run_dir / "ml-worker.log"
    logger.info(f"Writing logs to {log_path}")
    pid_file = PIDLockFile(create_pid_file_path(host, port))

    with DaemonContext(pidfile=pid_file, stdout=open(log_path, 'w+t')):
        logger.info(f"Daemon PID: {os.getpid()}")
        asyncio.get_event_loop().run_until_complete(start_ml_worker(host, port))
