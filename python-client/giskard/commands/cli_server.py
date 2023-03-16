import os
from pathlib import Path

import click
import requests
from python_on_whales import DockerClient

dockerfile_location = os.path.expanduser("~/giskard-home/docker/docker-compose.yml")
envfile_location = os.path.expanduser("~/giskard-home/docker/.env")
# TODO: Maybe make it into a release branch to not get a "nightly" one ?
dockerfile_url = "https://raw.githubusercontent.com/Giskard-AI/giskard/main/docker-compose.yml"
envfile_url = "https://raw.githubusercontent.com/Giskard-AI/giskard/main/.env"

client = DockerClient(compose_files=[dockerfile_location])


@click.group("server", help="Giskard UI management", context_settings={"show_default": True})
def server() -> None:
    """
    Giskard UI management
    """


@server.command("start")
def start():
    # Check if Giskard is already running
    client.compose.up(detach=True)
    ## If it is, exit
    # Check if Giskard is already installed
    ## If it isn't, install
    # Run Giskard
    pass


@server.command("stop")
def stop():
    client.compose.down()


@server.command("restart")
def restart():
    print("Not implemented yet.")


@server.command("logs")
def logs():
    print("Not implemented yet.")


@server.command("install")
def install():
    _install()


def _install():
    Path(os.path.expanduser("~/giskard-home/docker")).mkdir(parents=True, exist_ok=True)
    _get_dockerfile()
    client.compose.pull()


def _get_dockerfile():
    r = requests.get(dockerfile_url, allow_redirects=True)
    open(dockerfile_location, 'wb').write(r.content)
    r = requests.get(envfile_url, allow_redirects=True)
    open(envfile_location, 'wb').write(r.content)
