import asyncio
import collections
import functools
import hashlib
import logging
import os
import sys
from time import sleep

import click
from lockfile.pidlockfile import PIDLockFile
from pydantic import AnyHttpUrl, parse_obj_as

from giskard.path_utils import run_dir
from giskard.settings import settings

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("giskard").setLevel(logging.INFO)


def common_options(func):
    @click.option(
        "--verbose",
        "-v",
        is_flag=True,
        callback=set_verbose,
        default=False,
        expose_value=False,
        is_eager=True,
        help="Enable verbose logging",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def set_verbose(_ctx, _param, value):
    if value:
        logging.getLogger("giskard").setLevel(logging.DEBUG)


def remove_stale_pid_file(pid_file):
    pid = pid_file.read_pid()
    if pid is not None and is_pid_stale(pid):
        logger.debug("Stale PID file found, removing it")
        pid_file.break_lock()


def is_pid_stale(pid):
    try:
        os.kill(pid, 0)  # NOSONAR
    except (OSError, TypeError):
        return True
    else:
        return False


def create_pid_file_path(is_server, url):
    hash_value = ml_worker_id(is_server, url)
    return run_dir / f"ml-worker-{hash_value}.pid"


def ml_worker_id(is_server, url):
    key = f"{sys.executable}"
    if not is_server:
        key += str(url)
    hash_value = hashlib.sha1(key.encode()).hexdigest()
    return hash_value


def validate_url(_ctx, _param, value) -> AnyHttpUrl:
    return parse_obj_as(AnyHttpUrl, value)


def run_daemon(is_server, url, api_key, hf_token):
    from giskard.ml_worker.ml_worker import MLWorker
    from daemon import DaemonContext
    from daemon.daemon import change_working_directory

    log_path = get_log_path()
    logger.info(f"Writing logs to {log_path}")
    pid_file = PIDLockFile(create_pid_file_path(is_server, url))

    with DaemonContext(pidfile=pid_file, stdout=open(log_path, "w+t")):
        # For some reason requests.utils.should_bypass_proxies that's called inside every request made by requests
        # hangs when the process runs as a daemon. A dirty temporary fix is to disable proxies for daemon mode.
        # True reasons for this to happen to be investigated
        os.environ["no_proxy"] = "*"

        workdir = settings.home_dir / "tmp" / f"daemon-run-{os.getpid()}"
        workdir.mkdir(exist_ok=True, parents=True)
        change_working_directory(workdir)

        logger.info(f"Daemon PID: {os.getpid()}")
        asyncio.get_event_loop().run_until_complete(MLWorker(is_server, url, api_key, hf_token).start())


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
