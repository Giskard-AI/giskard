from typing import Optional

import functools
import logging
import os
import platform
import sys

import click
import lockfile
import psutil
from click import INT, STRING
from lockfile.pidlockfile import PIDLockFile, read_pid_from_pidfile, remove_existing_pidfile
from pydantic import AnyHttpUrl

from giskard.cli_utils import (
    common_options,
    create_pid_file_path,
    follow_file,
    get_log_path,
    remove_stale_pid_file,
    run_daemon,
    tail,
    validate_url,
)
from giskard.path_utils import run_dir
from giskard.settings import settings
from giskard.utils.analytics_collector import analytics, anonymize

logger = logging.getLogger(__name__)


@click.group("worker", help="ML Worker management", context_settings={"show_default": True})
def worker() -> None:
    """
    ML Worker management
    """


def start_stop_options(func):
    @click.option(
        "--url",
        "-u",
        type=STRING,
        default="http://localhost:19000",
        help="Remote Giskard hub url",
        callback=validate_url,
    )
    @click.option(
        "--server",
        "-s",
        "is_server",
        is_flag=True,
        default=False,
        help="Server mode. Used by Giskard embedded ML Worker",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@worker.command("start")
@common_options
@start_stop_options
@click.option(
    "--key",
    "-k",
    "api_key",
    envvar="GSK_API_KEY",
    help="Giskard hub API key",
)
@click.option(
    "--daemon",
    "-d",
    "is_daemon",
    is_flag=True,
    default=False,
    help="Should ML Worker be started as a Daemon in a background",
)
@click.option(
    "--hf-token",
    "hf_token",
    envvar="GSK_HF_TOKEN",
    help="Access token for Giskard hosted in a private Hugging Face Spaces",
)
@click.option(
    "--parallelism",
    "nb_workers",
    default=None,
    help="Number of processes to use for parallelism (None for number of cpu)",
)
def start_command(url: AnyHttpUrl, is_server, api_key, is_daemon, hf_token, nb_workers):
    """\b
    Start ML Worker.

    ML Worker can be started in 2 modes:

    - server: used by default by an ML Worker shipped by Giskard. ML Worker acts as a server that Giskard connects to.

    - client: ML Worker acts as a client and should connect to a running Giskard instance
        by specifying this instance's host and port.
    """
    analytics.track(
        "giskard-worker:start",
        {"is_server": is_server, "url": anonymize(url), "is_daemon": is_daemon},
    )
    api_key = initialize_api_key(api_key, is_server)
    hf_token = initialize_hf_token(hf_token, is_server)
    _start_command(is_server, url, api_key, is_daemon, hf_token, int(nb_workers) if nb_workers is not None else None)


def initialize_api_key(api_key, is_server):
    if is_server:
        return None
    if not api_key:
        api_key = click.prompt("Enter Giskard hub API key", type=str)
    if "GSK_API_KEY" in os.environ:
        # delete API key environment variable so that it doesn't get leaked when the test code is executed
        del os.environ["GSK_API_KEY"]
    return api_key


def initialize_hf_token(hf_token, is_server):
    if is_server:
        return None
    # HF token is not mandantory unless connection error
    if "GSK_HF_TOKEN" in os.environ:
        # delete HF token environment variable so that it doesn't get leaked when the test code is executed
        del os.environ["GSK_HF_TOKEN"]
    return hf_token


def _start_command(is_server, url: AnyHttpUrl, api_key, is_daemon, hf_token=None, nb_workers=None):
    from giskard.ml_worker.ml_worker import MLWorker

    os.environ["TQDM_DISABLE"] = "1"
    start_msg = "Starting ML Worker"
    start_msg += " server" if is_server else " client"
    if is_daemon:
        start_msg += " daemon"
    logger.info(start_msg)
    logger.info(f"Python: {sys.executable} ({platform.python_version()})")
    logger.info(f"Giskard Home: {settings.home_dir}")
    pid_file_path = create_pid_file_path(is_server, url)
    pid_file = PIDLockFile(pid_file_path)
    remove_stale_pid_file(pid_file)

    ml_worker: Optional[MLWorker] = None
    try:
        pid_file.acquire()
        if is_daemon:
            # Releasing the lock because it will be re-acquired by a daemon process
            pid_file.release()
            # If on windows, throw error and exit
            if sys.platform == "win32":
                logger.error("Daemon mode is not supported on Windows.")
                return

            run_daemon(is_server, url, api_key, hf_token)
        else:
            if sys.platform == "win32":
                from asyncio import run
            else:
                from uvloop import run
            run(_start_worker(is_server, url, api_key, hf_token, nb_workers))
    except KeyboardInterrupt:
        logger.info("Exiting")
        if ml_worker:
            ml_worker.stop()
    except lockfile.AlreadyLocked:
        existing_pid = read_pid_from_pidfile(pid_file_path)
        logger.warning(
            f"Another ML Worker {_ml_worker_description(is_server, url)} "
            f"is already running with PID: {existing_pid}. "
            "Not starting a new one. "
            'To stop a running worker for this instance execute: "giskard worker stop" or '
            '"giskard worker stop -a" to stop all running workers'
        )
    finally:
        if pid_file.i_am_locking():
            pid_file.release()


def _ml_worker_description(is_server, url):
    return "server" if is_server else f"client for {url}"


async def _start_worker(is_server, url, api_key, hf_token, nb_workers):
    from giskard.ml_worker.ml_worker import MLWorker

    ml_worker = MLWorker(is_server, url, api_key, hf_token)
    await ml_worker.start(nb_workers, restart=True)


@worker.command("stop", help="Stop running ML Workers")
@common_options
@start_stop_options
@click.option("--all", "-a", "stop_all", is_flag=True, default=False, help="Stop all running ML Workers")
def stop_command(is_server, url, stop_all):
    import re

    analytics.track(
        "giskard-worker:stop",
        {"is_server": is_server, "url": anonymize(url), "stop_all": stop_all},
    )
    if stop_all:
        for pid_fname in os.listdir(run_dir):
            if not re.match(r"^ml-worker-.*\.pid$", pid_fname):
                continue
            _stop_pid_fname(pid_fname)
    else:
        _find_and_stop(is_server, url)


@worker.command("restart", help="Restart ML Worker")
@common_options
@start_stop_options
@click.option("--api-key", "-k", "api_key", help="Giskard hub API key")
@click.option(
    "--hf-token",
    "hf_token",
    help="Access token for Giskard hosted in a private Hugging Face Spaces",
)
def restart_command(is_server, url, api_key, hf_token):
    analytics.track(
        "giskard-worker:restart",
        {"is_server": is_server, "url": anonymize(url)},
    )
    api_key = initialize_api_key(api_key, is_server)

    _find_and_stop(is_server, url)
    _start_command(is_server, url, api_key, is_daemon=True, hf_token=hf_token)


def _stop_pid_fname(pid_fname):
    pid_file_path = str(run_dir / pid_fname)
    remove_stale_pid_file(PIDLockFile(pid_file_path))
    pid = read_pid_from_pidfile(pid_file_path)
    if pid:
        worker_process = psutil.Process(pid)
        worker_process.terminate()
        logger.info(f"Stopped ML Worker Daemon by PID: {pid}")
    remove_existing_pidfile(pid_file_path)


def _find_and_stop(is_server, url):
    pid_file_path = str(create_pid_file_path(is_server, url))
    remove_stale_pid_file(PIDLockFile(pid_file_path))
    pid = read_pid_from_pidfile(pid_file_path)
    logger.info("Stopping ML Worker Daemon")
    if pid:
        worker_process = psutil.Process(pid)
        worker_process.terminate()
        logger.info(f"Stopped ML Worker {_ml_worker_description(is_server, url)}")
    else:
        logger.info(f"ML Worker {_ml_worker_description(is_server, url)} is not running")
    remove_existing_pidfile(pid_file_path)


@worker.command("logs")
@common_options
@click.option(
    "--lines",
    "-n",
    type=INT,
    default=10,
    help="Output the last N lines of the log file, 10 lines are displayed by default",
)
@click.option(
    "--follow",
    "-f",
    "is_follow",
    is_flag=True,
    default=False,
    help="Output appended data as new logs are being generated",
)
def read_logs(lines, is_follow):
    analytics.track(
        "giskard-worker:logs",
        {
            "lines": lines,
            "is_follow": is_follow,
        },
    )
    log_path = get_log_path()

    if not os.path.exists(log_path):
        print(f"Unable to find any logfile!\n{log_path} does not exists")
        exit(-1)

    for line in tail(log_path, lines):
        print(line, end="")

    if is_follow:
        follow_file(log_path)
