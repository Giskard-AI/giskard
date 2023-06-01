import platform

import click

import giskard
from giskard.commands.cli_server import server
from giskard.commands.cli_worker import worker
from giskard.path_utils import run_dir

# import sys
# from typing import Optional
#
# import click
# import lockfile
# import psutil
# from click import INT, STRING
# from lockfile.pidlockfile import PIDLockFile, read_pid_from_pidfile, remove_existing_pidfile
# from pydantic import AnyHttpUrl
#
# import giskard
# from giskard.cli_utils import create_pid_file_path, remove_stale_pid_file, run_daemon, get_log_path, tail, follow_file
# from giskard.cli_utils import validate_url
# from giskard.client.analytics_collector import GiskardAnalyticsCollector, anonymize

run_dir.mkdir(parents=True, exist_ok=True)


@click.group("cli")
@click.version_option(f"{giskard.__version__} (Python {platform.python_version()})")
def cli():
    """
    Giskard Command Line
    """


# Add all command groups here.
cli.add_command(worker)
cli.add_command(server)

if __name__ == "__main__":
    cli(auto_envvar_prefix="GSK")
