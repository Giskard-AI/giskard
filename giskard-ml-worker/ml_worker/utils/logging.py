import logging
import os
from datetime import timedelta
from functools import wraps
from logging.config import fileConfig
from timeit import default_timer

import sys


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


timer_logger = logging.getLogger("timer")


class Timer:
    message_template: str

    def __init__(self, message=None, start=True, level=logging.INFO) -> None:
        if start:
            self.start()
        else:
            self.__start_time = None
        self.duration = None
        self.message_template = message
        self.message = None
        self.level = level

    def start(self):
        self.__start_time = default_timer()

    def stop(self, message=None, log=True):
        if message:
            self.message_template = message
        if not self.__start_time:
            timer_logger.error("Timer was not started")
            return

        self.duration = timedelta(seconds=default_timer() - self.__start_time)
        if log:
            self.message = self.create_message(self.duration)
            timer_logger.log(self.level, self.message)
        return self.duration

    def __enter__(self):
        if not self.__start_time:
            self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def create_message(self, duration):
        if self.message_template:
            return self.message_template.strip() + f" executed in {duration}"
        else:
            return f"Executed in {duration}"

    def prepare_message_template(self):
        return self.message_template


def timer(message=None):
    def timing_decorator(f):
        @wraps(timing_decorator)
        def wrap(*args, **kw):
            with Timer(message if message else f'{f.__name__}'):
                result = f(*args, **kw)
            return result

        return wrap

    return timing_decorator
