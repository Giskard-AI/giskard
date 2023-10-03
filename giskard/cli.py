import platform

import click

import giskard
from giskard.core.errors import GiskardInstallationError

try:
    from giskard.commands.cli_server import server
    from giskard.commands.cli_worker import worker
except ImportError as e:
    raise GiskardInstallationError(flavor="server", functionality="Server") from e
from giskard.path_utils import run_dir

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
