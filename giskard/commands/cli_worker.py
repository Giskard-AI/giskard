from typing import Optional

import functools
import logging
import os
import platform
import sys
from pathlib import Path

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
    tail,
    validate_url,
)
from giskard.client.giskard_client import GiskardClient
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
        "--name",
        "worker_name",
        default="external_worker",
        help="Name/id of the worker starting",
    )
    @click.option(
        "--key",
        "-k",
        "api_key",
        envvar="GSK_API_KEY",
        help="Giskard hub API key",
    )
    @click.option(
        "--hf-token",
        "hf_token",
        envvar="GSK_HF_TOKEN",
        help="Access token for Giskard hosted in a private Hugging Face Spaces",
    )
    @click.option(
        "--server",
        "-s",
        "is_server",
        is_flag=True,
        default=False,
        help="Server mode. Used to control Giskard managed ML Worker",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def start_options(func):
    @click.option(
        "--parallelism",
        "nb_workers",
        default=None,
        help="Number of processes to use for parallelism (None for number of cpu)",
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
        "--log-level",
        "log_level",
        default=logging.getLevelName(logging.INFO),
        type=click.Choice(
            [
                logging.getLevelName(logging.DEBUG),
                logging.getLevelName(logging.INFO),
                logging.getLevelName(logging.WARNING),
                logging.getLevelName(logging.ERROR),
            ]
        ),
        help="Global log level",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@worker.command("start")
@common_options
@start_stop_options
@start_options
def start_command(url: AnyHttpUrl, is_server, api_key, is_daemon, hf_token, nb_workers, worker_name, log_level):
    """\b
    Start ML Worker.

    ML Worker can be started in 2 modes:

    - server: Giskard starts an ML Worker managed by itself on the server.

    - client: ML Worker acts as a client and should connect to a running Giskard instance
        by specifying this instance's host and port.
    """
    analytics.track(
        "giskard-worker:start",
        {"url": anonymize(url), "log_level": log_level},
    )

    logging.root.setLevel(logging.getLevelName(log_level))

    api_key = initialize_api_key(api_key)
    hf_token = initialize_hf_token(hf_token)
    if is_server:
        # Create a Giskard client and request to start an ML worker with given name
        _start_server_command(worker_name, url, api_key, hf_token)
    else:
        _start_command(
            worker_name, url, api_key, is_daemon, hf_token, int(nb_workers) if nb_workers is not None else None
        )


def initialize_api_key(api_key):
    if not api_key:
        api_key = click.prompt("Enter Giskard hub API key", type=str)
    if "GSK_API_KEY" in os.environ:
        # delete API key environment variable so that it doesn't get leaked when the test code is executed
        del os.environ["GSK_API_KEY"]
    return api_key


def initialize_hf_token(hf_token):
    # HF token is not mandantory unless connection error
    if "GSK_HF_TOKEN" in os.environ:
        # delete HF token environment variable so that it doesn't get leaked when the test code is executed
        del os.environ["GSK_HF_TOKEN"]
    return hf_token


def _start_server_command(worker_name, url: AnyHttpUrl, api_key, hf_token=None):
    client: GiskardClient = GiskardClient(str(url), api_key, hf_token)
    client.start_managed_worker(worker_name)


def _start_command(worker_name, url: AnyHttpUrl, api_key, is_daemon, hf_token=None, nb_workers=None):
    from giskard.ml_worker.ml_worker import MLWorker

    start_msg = f"Starting ML Worker {worker_name}"
    if is_daemon:
        start_msg += " daemon"
    logger.info(start_msg)

    os.environ["TQDM_DISABLE"] = "1"
    logger.info("Python: %s (%s)", sys.executable, platform.python_version())
    logger.info("Giskard Home: %s", settings.home_dir)

    pid_file_path = create_pid_file_path(worker_name, url)
    logger.info("Creating pid file : %s", pid_file_path)

    pid_file = PIDLockFile(pid_file_path)
    remove_stale_pid_file(pid_file)

    log_path = get_log_path(worker_name=worker_name)
    logger.info(f"Writing logs to {log_path}")

    ml_worker: Optional[MLWorker] = None
    try:
        pid_file.acquire()
        if settings.force_asyncio_event_loop or sys.platform == "win32":
            logger.info("Using asyncio to run jobs")
            from asyncio import run
        else:
            logger.info("Using uvloop to run jobs")
            from uvloop import run

        if is_daemon:
            from daemon import DaemonContext
            from daemon.daemon import change_working_directory

            # Releasing the lock because it will be re-acquired by a daemon process
            pid_file.release()

            # If on windows, throw error and exit
            if sys.platform == "win32":
                logger.error("Daemon mode is not supported on Windows.")
                return

            with DaemonContext(pidfile=pid_file, stdout=open(log_path, "w+t")):
                # For some reason requests.utils.should_bypass_proxies that's called inside every request made by requests
                # hangs when the process runs as a daemon. A dirty temporary fix is to disable proxies for daemon mode.
                # True reasons for this to happen to be investigated
                os.environ["no_proxy"] = "*"

                workdir = settings.home_dir / "tmp" / f"daemon-run-{os.getpid()}"
                workdir.mkdir(exist_ok=True, parents=True)
                change_working_directory(workdir)

                logger.info(f"Daemon PID: {os.getpid()}")
                run(_start_worker(worker_name, url, api_key, hf_token, nb_workers))
        else:
            run(_start_worker(worker_name, url, api_key, hf_token, nb_workers))
    except KeyboardInterrupt:
        logger.info("Exiting")
        if ml_worker:
            ml_worker.stop()
    except lockfile.AlreadyLocked:
        existing_pid = read_pid_from_pidfile(pid_file_path)
        logger.warning(
            f"Another ML Worker {_ml_worker_description(worker_name, url)} "
            f"is already running with PID: {existing_pid}. "
            "Not starting a new one. "
            'To stop a running worker for this instance execute: "giskard worker stop" or '
            '"giskard worker stop -a" to stop all running workers'
        )
    finally:
        if pid_file.i_am_locking():
            pid_file.release()


def _ml_worker_description(worker_name: str, url: AnyHttpUrl):
    return f"named {worker_name} for {url}"


async def _start_worker(worker_name, url, api_key, hf_token, nb_workers):
    from giskard.ml_worker.ml_worker import MLWorker

    ml_worker = MLWorker(worker_name, url, api_key, hf_token)
    await ml_worker.start(restart=True, nb_workers=nb_workers)


def _stop_server_command(worker_name, url: AnyHttpUrl, api_key, hf_token=None):
    client: GiskardClient = GiskardClient(str(url), api_key, hf_token)
    return client.stop_managed_worker(worker_name)


@worker.command("stop", help="Stop running ML Workers")
@common_options
@start_stop_options
@click.option("--all", "-a", "stop_all", is_flag=True, default=False, help="Stop all running ML Workers")
def stop_command(worker_name, stop_all, is_server, url: AnyHttpUrl, api_key, hf_token=None):
    import re

    analytics.track(
        "giskard-worker:stop",
        {"url": anonymize(url), "stop_all": stop_all},
    )
    if stop_all:
        if is_server:
            logger.fatal("Stopping all workers on the server is not yet supported.")
            return
        for pid_path in run_dir.iterdir():
            if not re.match(r"^ml-worker-.*\.pid$", pid_path.name):
                continue
            _stop_pid_fname(pid_path)
    else:
        if is_server:
            api_key = initialize_api_key(api_key)
            hf_token = initialize_hf_token(hf_token)
            _stop_server_command(worker_name, url, api_key, hf_token)
        else:
            _find_and_stop(worker_name, url)


def _restart_server_command(worker_name, url: AnyHttpUrl, api_key, hf_token=None):
    client: GiskardClient = GiskardClient(url, api_key, hf_token)
    client.stop_managed_worker(worker_name)
    client.start_managed_worker(worker_name)


@worker.command("restart", help="Restart ML Worker")
@common_options
@start_stop_options
@start_options
def restart_command(url: AnyHttpUrl, is_server, api_key, is_daemon, hf_token, nb_workers, worker_name, log_level):
    analytics.track(
        "giskard-worker:restart",
        {"url": anonymize(url)},
    )
    logging.root.setLevel(logging.getLevelName(log_level))

    if is_server:
        _restart_server_command(worker_name, url, api_key, hf_token)
        return

    # Restart the local worker
    _find_and_stop(worker_name, url)
    _start_command(worker_name, url, api_key, is_daemon, hf_token=hf_token, nb_workers=nb_workers)


def _stop_pid_fname(pid_path: Path):
    pid_file_path = str(pid_path)
    remove_stale_pid_file(PIDLockFile(pid_path))
    pid = read_pid_from_pidfile(pid_path)
    if pid:
        worker_process = psutil.Process(pid)
        worker_process.terminate()
        logger.info("Stopped ML Worker by PID: %s", pid)
    else:
        logger.info("ML Worker (PID %s, path %s) is not running", pid, pid_path)
    remove_existing_pidfile(pid_file_path)


def _find_and_stop(worker_name: str, url: AnyHttpUrl):
    return _stop_pid_fname(create_pid_file_path(worker_name, url))


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
