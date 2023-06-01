import logging
import os
from pathlib import Path

import click
import requests
from python_on_whales import DockerClient

giskard_home_path = os.path.expanduser("~/giskard-home")
dockerfile_location = giskard_home_path + "/docker/docker-compose.yml"
envfile_location = giskard_home_path + "/docker/.env"

# TODO: Maybe make it into a release branch to not get a "nightly" one ?
dockerfile_url = "https://raw.githubusercontent.com/Giskard-AI/giskard/main/docker-compose.yml"
envfile_url = "https://raw.githubusercontent.com/Giskard-AI/giskard/main/.env"

client = DockerClient(compose_files=[dockerfile_location])

logger = logging.getLogger(__name__)


@click.group("server", help="Giskard UI management", context_settings={"show_default": True})
def server() -> None:
    """
    Giskard UI management
    """


def start_options(fn):
    fn = click.option(
        "--attach",
        "-a",
        "attached",
        is_flag=True,
        default=False,
        help="Starts the server and attaches to it, displaying logs in console.",
    )(fn)
    return fn


def update_options(fn):
    fn = click.option(
        "--version",
        "-v",
        "version",
        is_flag=False,
        default="",
        help="Version to update to."
    )(fn)
    return fn


@server.command("start")
@start_options
def start(attached):
    """\b
    Start Giskard Server.

    By default, the server starts detached and will run in the background.
    You can attach to it by using -a
    """
    logger.info("Starting Giskard Server")
    # TODO: Update to check for installation/grabbing latest
    # if not _check_downloaded():
    #     _update()

    client.compose.up(detach=not attached)


@server.command("stop")
def stop():
    """\b
    Stop Giskard Server.

    Stops any running Giskard server. Does nothing if Giskard server is not running.
    """
    logger.info("Stopping Giskard Server")
    client.compose.down()


@server.command("restart")
def restart():
    """\b
    Restart Giskard Server.

    Stops any running Giskard server and starts it again.
    """
    logger.info("Restarting Giskard Server")
    client.compose.restart()


@server.command("logs")
def logs():
    print("Not implemented yet.")


@server.command("update")
@update_options
def update(version):
    """\b
    Updates Giskard Server
    """
    if version == "":
        version = _fetch_latest_tag()

    logger.info(f"Updating Giskard Server to version {version}")
    if not _check_downloaded():
        _download_dockerfile(version)
    client.compose.pull()
    logger.info("Giskard Server updated.")


def _check_downloaded():
    return False
    # if not os.path.exists(dockerfile_location) or not os.path.exists(envfile_location):
    #     return False
    # return True


def _download_dockerfile(version):
    logger.info(f"Downloading files for version {version}")
    Path(os.path.expanduser("~/giskard-home/docker")).mkdir(parents=True, exist_ok=True)
    r = requests.get(f"https://raw.githubusercontent.com/Giskard-AI/giskard/{version}/docker-compose.yml",
                     allow_redirects=True)
    open(dockerfile_location, 'wb').write(r.content)
    r = requests.get(f"https://raw.githubusercontent.com/Giskard-AI/giskard/{version}/.env", allow_redirects=True)
    open(envfile_location, 'wb').write(r.content)


# Returns the latest tag from the GitHub API
# Format: vX.Y.Z
def _fetch_latest_tag() -> str:
    response = requests.get("https://api.github.com/repos/Giskard-AI/giskard/releases/latest")
    response.raise_for_status()
    json_response = response.json()
    tag = json_response["tag_name"]
    return tag
