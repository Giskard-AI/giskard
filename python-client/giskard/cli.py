import asyncio
import logging
import os
import platform
import sys

import click
import lockfile
import psutil
from click import STRING
from lockfile.pidlockfile import PIDLockFile, read_pid_from_pidfile, remove_existing_pidfile
from pydantic import AnyHttpUrl

from giskard.cli_utils import create_pid_file_path, remove_stale_pid_file, run_daemon, validate_url
from giskard.client.analytics_collector import GiskardAnalyticsCollector, anonymize
from giskard.ml_worker.ml_worker import start_ml_worker
from giskard.path_utils import run_dir
from giskard.settings import settings

run_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
analytics = GiskardAnalyticsCollector()


def set_verbose(_ctx, _param, value):
    if value:
        logging.getLogger().setLevel(logging.DEBUG)


@click.group("cli")
def cli():
    """
    Giskard Command Line
    """


@cli.group("worker", help="ML Worker management", context_settings={"show_default": True})
def worker() -> None:
    """
    ML Worker management
    """


def start_stop_options(fn):
    fn = click.option(
        "--url", "-u", type=STRING, default='http://localhost:19000', help="Remote Giskard server url",
        callback=validate_url
    )(fn)
    fn = click.option(
        "--server", "-s", "is_server", is_flag=True, default=False,
        help="Server mode. Used by Giskard embedded ML Worker"
    )(fn)
    fn = click.option(
        "--verbose",
        "-v",
        is_flag=True,
        callback=set_verbose,
        default=False,
        expose_value=False,
        is_eager=True,
        help="Enable verbose logging",
    )(fn)
    return fn


@worker.command("start")
@start_stop_options
@click.option(
    "--key",
    "-k",
    "api_key",
    prompt="Enter Giskard server API key",
    envvar='GSK_API_KEY',
    help="Giskard server API key",
)
@click.option(
    "--daemon",
    "-d",
    "is_daemon",
    is_flag=True,
    default=False,
    help="Should ML Worker be started as a Daemon in a background",
)
def start_command(url: AnyHttpUrl, is_server, api_key, is_daemon):
    """\b
    Start ML Worker.

    ML Worker can be started in 2 modes:

    - server: used by default by an ML Worker shipped by Giskard. ML Worker acts as a server that Giskard connects to.

    - client: ML Worker acts as a client and should connect to a running Giskard instance
        by specifying this instance's host and port.
    """

    if 'GSK_API_KEY' in os.environ:
        # delete API key environment variable so that it doesn't get leaked when the test code is executed
        del os.environ['GSK_API_KEY']
    _start_command(is_server, url, api_key, is_daemon)


def _start_command(is_server, url: AnyHttpUrl, api_key, is_daemon):
    analytics.track("Start ML Worker", {
        "is_server": is_server,
        "url": anonymize(url),
        "is_daemon": is_daemon
    }, force=True)

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
    try:
        pid_file.acquire()
        if is_daemon:
            # Releasing the lock because it will be re-acquired by a daemon process
            pid_file.release()
            run_daemon(is_server, url, api_key)
        else:
            loop = asyncio.new_event_loop()
            loop.create_task(start_ml_worker(is_server, url, api_key))
            loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Exiting")
    except lockfile.AlreadyLocked:
        existing_pid = read_pid_from_pidfile(pid_file_path)
        logger.warning(
            f"Another ML Worker {_ml_worker_description(is_server, url)} "
            f"is already running with PID: {existing_pid}. "
            f"Not starting a new one."
        )
    finally:
        if pid_file.i_am_locking():
            pid_file.release()


def _ml_worker_description(is_server, url):
    return "server" if is_server else f"client for {url}"


@worker.command("stop", help="Stop running ML Workers")
@start_stop_options
@click.option(
    "--all", "-a", "stop_all", is_flag=True, default=False, help="Stop all running ML Workers"
)
def stop_command(is_server, url, stop_all):
    import re

    if stop_all:
        for pid_fname in os.listdir(run_dir):
            if not re.match(r"^ml-worker-.*\.pid$", pid_fname):
                continue
            _stop_pid_fname(pid_fname)
    else:
        _find_and_stop(is_server, url)


@worker.command("restart", help="Restart ML Worker")
@start_stop_options
@click.option(
    "--api-key",
    "-k",
    "api_key",
    prompt="Enter Giskard server API key",
    help="Giskard server API key"
)
def restart_command(is_server, url, api_key):
    _find_and_stop(is_server, url)
    _start_command(is_server, url, api_key, is_daemon=True)


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


if __name__ == "__main__":
    cli(auto_envvar_prefix="GSK")
