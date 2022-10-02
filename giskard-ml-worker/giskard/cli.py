import asyncio
import logging
import os

import click
import lockfile
import psutil
from click import STRING, INT
from lockfile.pidlockfile import PIDLockFile, read_pid_from_pidfile, remove_existing_pidfile

from giskard.cli_utils import remove_stale_pid_file, create_pid_file_path, run_daemon
from giskard.ml_worker.ml_worker import start_ml_worker
from giskard.settings import run_dir

run_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


@click.group("cli")
def cli():
    pass


def set_verbose(_ctx, _param, value):
    if value:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.group("worker", help="ML Worker management")
@click.option('--verbose', '-v', is_flag=True, callback=set_verbose, default=False,
              expose_value=False, is_eager=True, help='Enable verbose logging')
def worker() -> None:
    pass


@worker.command("start", context_settings={'show_default': True})
@click.option('--host', '-h', type=STRING, help='Remote Giskard host address to connect to')
@click.option('--port', '-p', type=INT, default=40051,
              help='Remote Giskard port accepting external ML Worker connections')
@click.option('--daemon', '-d', 'is_daemon', is_flag=True, default=False,
              help='Should ML Worker be started as a Daemon in a background')
def start_command(host, port, is_daemon):
    """\b
    Start ML Worker.

    ML Worker can be started in 2 modes:

    - internal: used by default by an ML Worker shipped by Giskard. ML Worker acts as a server that Giskard connects to.

    - external: ML Worker acts as a client and should connect to a running Giskard instance
        by specifying this instance's host and port.
    """

    logger.info("Starting ML Worker" + (" as daemon" if is_daemon else ""))
    pid_file_path = create_pid_file_path(host, port)
    pid_file = PIDLockFile(pid_file_path)
    remove_stale_pid_file(pid_file)

    try:
        pid_file.acquire()
        if is_daemon:
            # Releasing the lock because it will be re-acquired by a daemon process
            pid_file.release()
            run_daemon(host, port)
        else:
            asyncio.get_event_loop().run_until_complete(start_ml_worker(host, port))
    except KeyboardInterrupt:
        logger.info("Exiting")
    except lockfile.AlreadyLocked:
        existing_pid = read_pid_from_pidfile(pid_file_path)
        logger.warning(
            f"Another ML Worker for {host or ''}:{port or ''} is already running with PID: {existing_pid}. Not starting a new one.")
    finally:
        if pid_file.i_am_locking():
            pid_file.release()


@worker.command("stop", help="Stop running ML Workers", context_settings={'show_default': True})
@click.option('--host', '-h', type=STRING, help='Remote Giskard host Giskard is connected to')
@click.option('--port', '-p', type=INT, default=40051, help='Remote Giskard port')
@click.option('--all', '-a', 'stop_all', is_flag=True, default=False, help='Stop all running ML Workers')
def stop_command(host, port, stop_all):
    import re
    if stop_all:
        for pid_fname in os.listdir(run_dir):
            if not re.match(r'^ml-worker-.*\.pid$', pid_fname):
                continue
            _stop_pid_fname(pid_fname)
    else:
        _find_and_stop(host, port)


def _stop_pid_fname(pid_fname):
    pid_file_path = str(run_dir / pid_fname)
    remove_stale_pid_file(PIDLockFile(pid_file_path))
    pid = read_pid_from_pidfile(pid_file_path)
    if pid:
        logger.info(f"Stopping ML Worker Daemon by PID: {pid}")
        worker_process = psutil.Process(pid)
        worker_process.terminate()
        logger.info(f"Stopped")
    remove_existing_pidfile(pid_file_path)


def _find_and_stop(host, port):
    pid_file_path = str(create_pid_file_path(host, port))
    remove_stale_pid_file(PIDLockFile(pid_file_path))
    pid = read_pid_from_pidfile(pid_file_path)
    logger.info("Stopping ML Worker Daemon")
    if pid:
        worker_process = psutil.Process(pid)
        worker_process.terminate()
        logger.info(f"Stopped ML Worker for {host or ''}:{port or ''}")
    else:
        logger.info(f"ML Worker is not running for {host or ''}:{port or ''}")
    remove_existing_pidfile(pid_file_path)


if __name__ == '__main__':
    cli()
