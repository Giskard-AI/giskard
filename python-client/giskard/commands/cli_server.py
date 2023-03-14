import click

from python_on_whales import docker


@click.group("server", help="Giskard UI management", context_settings={"show_default": True})
def server() -> None:
    """
    Giskard UI management
    """


@server.command("start")
def start():
    # Check if Giskard is already running
    docker.compose.start()
    ## If it is, exit
    # Check if Giskard is already installed
    ## If it isn't, install
    # Run Giskard
    pass


@server.command("stop")
def stop():
    # Check if Giskard is already running
    ## If it isn't, exit
    # Stop Giskard
    pass


@server.command("restart")
def restart():
    pass


@server.command("logs")
def logs():
    pass


@server.command("install")
def install():
    pass
