import logging
import os
from typing import Optional

import click
import requests
import yaml
from docker import DockerClient
from docker.errors import NotFound, DockerException

from giskard.cli_utils import common_options
from giskard.settings import settings

logger = logging.getLogger(__name__)

giskard_settings_path = settings.home_dir / "server-settings.yml"
IMAGE_NAME = "docker.io/giskardai/giskard"

docker_client: Optional[DockerClient] = None
try:
    import docker

    docker_client = docker.from_env()
except DockerException as e:
    logger.error("Failed to connect to Docker: ", e)


@click.group("server", help="Giskard UI management", context_settings={"show_default": True})
def server() -> None:
    """
    Giskard UI management
    """


def update_options(fn):
    fn = click.option(
        "--version",
        "version",
        is_flag=False,
        default="",
        help="Version to update to."
    )(fn)
    return fn


@server.command("start")
@common_options
@click.option("--attach",
              "-a",
              "attached",
              is_flag=True,
              default=False,
              help="Starts the server and attaches to it, displaying logs in console.")
def start(attached):
    """\b
    Start Giskard Server.

    By default, the server starts detached and will run in the background.
    You can attach to it by using -a
    """
    logger.info("Starting Giskard Server")
    app_settings = _get_settings()
    if not app_settings:
        version = _fetch_latest_tag()
        logger.info(f"Giskard Server not installed. Installing {version} now.")
        _write_settings({"version": version})
    else:
        version = app_settings["version"]

    _pull_image(version.replace('v', ''))

    home_volume = _get_home_volume()

    try:
        container = docker_client.containers.get(f"giskard-server.{version.replace('v', '')}")
    except:
        container = docker_client.containers.create(f"{IMAGE_NAME}:{version.replace('v', '')}",
                                                    detach=not attached,
                                                    name=f"giskard-server.{version.replace('v', '')}",
                                                    ports={7860: 19000},
                                                    volumes={
                                                        home_volume.name: {'bind': '/home/giskard/datadir',
                                                                           'mode': 'rw'}
                                                    })
    container.start()
    logger.info(f"Giskard Server {version} started. You can access it at http://localhost:19000")


@server.command("stop")
@common_options
def stop():
    """\b
    Stop Giskard Server.

    Stops any running Giskard server. Does nothing if Giskard server is not running.
    """

    version = _get_settings()["version"]
    try:
        container = docker_client.containers.get(f"giskard-server.{version.replace('v', '')}")
        if container.status != 'exited':
            logger.info("Stopping Giskard Server")
            container.stop()
        else:
            logger.info(f"Giskard {version} is not running")
    except NotFound:
        logger.info(f"Giskard {version} is not found")


@server.command("restart")
@common_options
def restart():
    """\b
    Restart Giskard Server.

    Stops any running Giskard server and starts it again.
    """
    logger.info("Restarting Giskard Server")
    container = docker_client.containers.get("giskard-server")
    container.stop()
    container.start()


@server.command("logs")
@common_options
@click.argument("service", default="backend", type=click.Choice(["backend", "frontend", "mlworker", "db"]),
                required=True)
def logs(service):
    """\b
    Prints logs for selected service.
    """
    logger.info(f"Logs for {service}")


@server.command("update")
@common_options
@click.option(
    "--version",
    "version",
    is_flag=False,
    default="",
    help="Version to update to.")
def update(version):
    """\b
    Updates Giskard Server
    """
    if version == "":
        version = _fetch_latest_tag()

    logger.info(f"Updating Giskard Server to version {version}")
    _pull_image(version.replace('v', ''))

    logger.info("Giskard Server updated.")  # Maybe offer to remove old containers here?


@server.command("info")
@common_options
def info():
    """\b
    Get information about the Giskard Server.
    """
    settings = _get_settings()
    if not settings:
        logger.info(f"Giskard Server is not installed. Install using $giskard server start")
        return
    else:
        version = settings["version"]

    logger.info(f"Giskard Server {version} is installed.")

    latest = _fetch_latest_tag()

    if version != latest:
        logger.info(f"A new version is available: {latest}")


def _check_downloaded(ver: str):
    tag = f"{IMAGE_NAME}:{ver}"
    try:
        docker_client.images.get(tag)
        logger.debug(f"Docker image exists: {tag}")
        return True
    except docker.errors.ImageNotFound:
        logger.debug(f"Docker image not found locally: {tag}")
        return False


# Version: X.Y.Z
def _pull_image(version):
    if not _check_downloaded(version):
        logger.info(f"Downloading image for version {version}")
        docker_client.images.pull(IMAGE_NAME, tag=version.replace('v', ''))


# Returns the latest tag from the GitHub API
# Format: vX.Y.Z
def _fetch_latest_tag() -> str:
    response = requests.get("https://api.github.com/repos/Giskard-AI/giskard/releases/latest")
    response.raise_for_status()
    json_response = response.json()
    tag = json_response["tag_name"]
    return tag


def _write_settings(settings):
    with open(giskard_settings_path, "w") as f:
        yaml.dump(settings, f)


def _get_settings():
    # Check the file exists first
    if not os.path.isfile(giskard_settings_path):
        return None

    return yaml.safe_load(open(giskard_settings_path, "r"))


def _get_home_volume():
    try:
        logger.debug("Found existing 'giskard-home' volume, reusing it")
        home_volume = docker_client.volumes.get("giskard-home")
    except NotFound:
        logger.info("Creating a new volume: 'giskard-home'")
        home_volume = docker_client.volumes.create("giskard-home")

    return home_volume
