from logging.config import fileConfig
from pathlib import Path


def path(p):
    return Path(__file__).parent / p


#fileConfig(path('../logging_config.ini'))
