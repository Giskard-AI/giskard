import logging
import os
import re
from pathlib import Path
from typing import Optional

import click
import docker
import requests
import yaml
from docker import DockerClient
from docker.errors import NotFound, DockerException
from docker.models.containers import Container
from tenacity import retry, wait_exponential

from giskard.cli_utils import common_options
from giskard.settings import settings

logger = logging.getLogger(__name__)

giskard_settings_path = settings.home_dir / "server-settings.yml"
IMAGE_NAME = "docker.io/giskardai/giskard"


def create_docker_client() -> DockerClient:
    try:
        return docker.from_env()
    except DockerException as e:
        raise RuntimeError("Failed to connect to Docker") from e


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


def get_version(version=None):
    if not version:
        app_settings = _get_settings()
        if not app_settings:
            version = _fetch_latest_tag()
            logger.info(f"Giskard Server not installed. Latest version is {version}")
            _write_settings({"version": version})
        else:
            version = app_settings["version"]
    else:
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        assert re.match(pattern, version), f"Invalid version format, version should match {pattern}"
        current_settings = _get_settings() or {}
        current_settings['version'] = version
        _write_settings(current_settings)
    return version


def get_container_name(version=None):
    if not version:
        version = get_version()
    return f"giskard-server.{version}"


def get_image_name(version=None):
    if not version:
        version = get_version()
    return f"{IMAGE_NAME}:{version}"


def get_container(version=None, quit_if_not_exists=True) -> Optional[Container]:
    name = get_container_name(version)
    try:
        return create_docker_client().containers.get(name)
    except NotFound:
        if quit_if_not_exists:
            logger.error(f"Container {name} could not be found. Run `giskard server start` to create the container")
            raise click.Abort()
        else:
            return None


def _start(attached=False, version=None):
    logger.info("Starting Giskard Server")

    settings = _get_settings() or {}
    port = settings.get('port', 19000)
    ml_worker_port = settings.get('ml_worker_port', 40051)

    version = get_version(version)

    _pull_image(version)

    home_volume = _get_home_volume()

    container = get_container(version, quit_if_not_exists=False)

    if not container:
        container = create_docker_client().containers.create(get_image_name(version),
                                                             detach=not attached,
                                                             name=get_container_name(version),
                                                             ports={7860: port,
                                                                    40051: ml_worker_port},
                                                             volumes={
                                                                 home_volume.name: {'bind': '/home/giskard/datadir',
                                                                                    'mode': 'rw'}
                                                             })
    container.start()
    logger.info(f"Giskard Server {version} started. You can access it at http://localhost:{port}")


def _check_downloaded(version: str):
    image = get_image_name(version)
    try:
        create_docker_client().images.get(image)
        logger.debug(f"Docker image exists: {image}")
        return True
    except docker.errors.ImageNotFound:
        logger.debug(f"Docker image not found locally: {image}")
        return False


# Version: X.Y.Z
def _pull_image(version):
    if not _check_downloaded(version):
        logger.info(f"Downloading image for version {version}")
        try:
            create_docker_client().images.pull(IMAGE_NAME, tag=version)
        except NotFound:
            logger.error(
                f"Image {get_image_name(version)} not found. Use a valid `--version` argument or check the content of $GSK_HOME/server-settings.yml")
            raise click.Abort()


@retry(wait=wait_exponential(min=0.1, max=5, multiplier=0.1))
def _fetch_latest_tag() -> str:
    """
    Returns: the latest tag from the GitHub API. Format: vX.Y.Z
    """
    response = requests.get("https://api.github.com/repos/Giskard-AI/giskard/releases/latest")
    response.raise_for_status()
    json_response = response.json()
    tag = json_response["tag_name"]
    return tag.replace('v', '')


def _write_settings(settings):
    with open(giskard_settings_path, "w") as f:
        yaml.dump(settings, f)


def _get_settings():
    # Check the file exists first
    if not os.path.isfile(giskard_settings_path):
        return None

    return yaml.safe_load(open(giskard_settings_path, "r"))


def _get_home_volume():
    docker_client = create_docker_client()
    try:
        logger.debug("Found existing 'giskard-home' volume, reusing it")
        home_volume = docker_client.volumes.get("giskard-home")
    except NotFound:
        logger.info("Creating a new volume: 'giskard-home'")
        home_volume = docker_client.volumes.create("giskard-home")

    return home_volume


@server.command("start")
@click.option("--attach", "-a", "attached",
              is_flag=True,
              default=False,
              help="Starts the server and attaches to it, displaying logs in console.")
@click.option("--version",
              "version",
              required=False,
              help="Version of Giskard server to start")
@common_options
def start(attached, version):
    """\b
    Start Giskard Server.

    By default, the server starts detached and will run in the background.
    You can attach to it by using -a
    """
    _start(attached, version)


@server.command("stop")
@common_options
def stop():
    """\b
    Stop Giskard Server.

    Stops a running Giskard server. Does nothing if Giskard server is not running.
    """
    container = get_container()
    if container.status != 'exited':
        logger.info("Stopping Giskard Server")
        container.stop()
        logger.info("Giskard Server stopped")
    else:
        logger.info(f"Giskard container {container.name} is not running")


@server.command("restart")
@click.argument("service",
                type=click.Choice(["backend", "frontend", "worker", "db"]),
                required=False)
@click.option("--hard", "hard",
              is_flag=True,
              default=False,
              help="Hard restart. Restarts the whole container")
@common_options
def restart(service, hard):
    """\b
    Restart Giskard Server.

    Stops any running Giskard server and starts it again.
    """
    container = get_container()
    if container.status != 'running':
        logger.info("Giskard server isn't running")
        _start()
    else:
        if hard:
            logger.info(f"Restarting {container.name} container")
            container.start()
            container.stop()
            if get_container():
                logger.info(f"Container {container.name} restarted")
        else:
            if service:
                logger.info(f"Restarting service {service} in {container.name} container")
                command = f"supervisorctl -c /opt/giskard/supervisord.conf restart {service}"
            else:
                logger.info(f"Restarting all services in {container.name} container")
                command = "supervisorctl -c /opt/giskard/supervisord.conf restart all"
            for res in container.exec_run(command, stream=True).output:
                print(res.decode())


@server.command("logs")
@click.argument("service",
                type=click.Choice(["backend", "frontend", "worker", "db"]),
                required=False)
@click.option("--lines",
              "-l",
              "nb_lines",
              default=300,
              type=click.IntRange(0),
              help="Number of log lines to show")
@click.option("--follow", "-f", "follow",
              is_flag=True,
              default=False,
              help="Follow the logs stream")
@common_options
def logs(service, nb_lines, follow):
    """\b
    Prints logs of server services
    """
    container = get_container()
    if not follow:
        if service:
            command = f"tail -{nb_lines} /home/giskard/datadir/run/{service}.log"
        else:
            command = "bash -c 'tail /home/giskard/datadir/run/*.log'"
        print(container.exec_run(command).output.decode())
    else:
        if service:
            command = f"tail -{nb_lines}f /home/giskard/datadir/run/{service}.log"
        else:
            command = "bash -c 'tail -f /home/giskard/datadir/run/*.log'"
        res = container.exec_run(command, stream=True)
        for out in res.output:
            print(out.decode())


@server.command("diagnose")
@click.option("--out_path",
              "-o",
              "local_dir",
              default=os.getcwd(),
              type=click.Path(),
              help="Destination directory to save diagnose archive to")
@common_options
def diagnose(local_dir):
    """\b
    Save server logs to a local archive (Useful for support).
    """
    out_dir = Path(local_dir)
    assert out_dir.is_dir(), "'output' should be an existing directory"
    bits, stat = get_container().get_archive("/home/giskard/datadir/run", encode_stream=True)
    from datetime import datetime

    now = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_file = out_dir / f"giskard-diagnose-{get_version().replace('.', '_')}-{now}.tar.gz"
    with open(out_file, 'wb') as f:
        for chunk in bits:
            f.write(chunk)
    logger.info(f"Wrote diagnose info to {out_file}")


@server.command("update")
@common_options
@click.argument(
    "version",
    required=False,
    default=None)
def update(version):
    """\b
    Update Giskard Server. Uses the latest available version if not specified.
    """
    latest_version = _fetch_latest_tag()
    if not version:
        version = latest_version

    installed_version = _get_settings().get('version')
    if installed_version == version:
        logger.info(f"Giskard server is already running version {version}")
        return

    logger.info(f"Updating Giskard Server {installed_version} -> {version}")
    _pull_image(version)
    _write_settings({**_get_settings(), **{"version": version}})
    logger.info(f"Giskard Server updated to {version}")


def convert_version_to_number(version: str) -> int:
    return int(''.join(re.findall(r'\d', version)))


@server.command("status")
@common_options
def status():
    """\b
    Check if server container is running and status of each internal service
    """
    app_settings = _get_settings()
    if not app_settings:
        logger.info("Giskard Server is not installed. Install using `giskard server start`")
        return
    else:
        version = app_settings["version"]

    logger.info(f"Giskard Server {version} is installed.")

    latest = _fetch_latest_tag()

    if convert_version_to_number(version) < convert_version_to_number(version):
        logger.info(f"A new version is available: {latest}")

    container = get_container()
    if container:
        if container.status == 'running':
            logger.info(F"Container {container.name} status:")
            print(get_container().exec_run("supervisorctl -c /opt/giskard/supervisord.conf").output.decode())
        else:
            logger.info(f"Container {container.name} isn't running ({container.status})")


@server.command("clean")
@click.option("--data", "delete_data",
              is_flag=True,
              help="Delete user data (giskard-home volume)")
@common_options
def clean(delete_data):
    """\b
    Delete Docker container, container (and possibly a volume) associated with the current version of Giskard Server
    """
    logger.info("Removing Giskard Server")
    client = create_docker_client()
    container_name = get_container_name()
    image_name = get_image_name()
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        logger.info(f"Container {container_name} has been deleted")
    except NotFound:
        logger.info(f"Container {container_name} does not exist")
    try:
        client.images.get(image_name).remove()
        logger.info(f"Image {image_name} has been deleted")
    except NotFound:
        logger.info(f"Image {image_name} does not exist")

    try:
        volume = client.volumes.get('giskard-home')
        if delete_data and click.confirm("Are you sure you want to delete user data (giskard-home volume)? "
                                         "This will permanently erase all of the Giskard activity results"):
            volume.remove()
            logger.info("User data has been deleted in 'giskard-home' volume")
    except NotFound:
        logger.info("Volume 'giskard-home' does not exist")
