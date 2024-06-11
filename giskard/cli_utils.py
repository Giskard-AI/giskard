import collections
import functools
import hashlib
import logging
import os
import sys
from pathlib import Path
from time import sleep

import click
from pydantic import AnyHttpUrl, parse_obj_as

from giskard.path_utils import run_dir

logger = logging.getLogger(__name__)
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


def create_pid_file_path(worker_name, url):
    hash_value = ml_worker_id(worker_name, url)
    return run_dir / f"ml-worker-{hash_value}.pid"


def ml_worker_id(worker_name, url):
    key = f"{sys.executable}{str(url)}{worker_name}"
    hash_value = hashlib.sha1(key.encode()).hexdigest()
    return hash_value


def validate_url(_ctx, _param, value) -> AnyHttpUrl:
    return parse_obj_as(AnyHttpUrl, value)


def get_log_path(worker_name=None):
    return run_dir / (f"ml-worker-{worker_name}.log" if worker_name else "ml-worker.log")


def tail(filename, n=100):
    """Return the last n lines of a file"""
    with Path(filename).open("r", encoding="utf-8") as fp:
        return collections.deque(fp, n)


def follow_file(filename):
    if not os.path.exists(filename):
        print(f"{filename} does not exists")
        return

    wait = 1
    with Path(filename).open("r", encoding="utf-8") as fp:
        exit_pooling = False
        skip_existing = True
        while not exit_pooling:
            line = fp.readline()

            if not line:
                skip_existing = False
                sleep(wait)
            elif not skip_existing:
                print(line, end="")
