import os
import sys
from logging.config import fileConfig


def resolve(filename):
    for directory in sys.path:
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            return path


def load_logging_config():
    from main import settings

    if settings.environment:
        config_path = resolve(f'logging_config{"." + settings.environment}.ini')
        if config_path:
            fileConfig(config_path)
        else:
            print(f"Failed to load logging config from {config_path}")
    else:
        fileConfig(resolve('logging_config.ini'))
