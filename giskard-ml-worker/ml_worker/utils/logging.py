import os
from logging.config import fileConfig

import sys


def resolve(filename):
    for directory in sys.path:
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            return path


def load_logging_config(env=None):
    if env is None:
        from main import settings
        env = settings.environment
    if env:
        config_path = resolve(f'logging_config{"." + env}.ini')
        if config_path:
            fileConfig(config_path)
        else:
            print(f"Failed to load logging config from {config_path}")
    else:
        fileConfig(resolve('logging_config.ini'))
