import logging
import sys
from datetime import timedelta
from functools import wraps
from timeit import default_timer

from giskard.settings import settings

logger = logging.getLogger(__name__)


def configure_logging():
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    logging.getLogger("shap").setLevel(logging.WARNING)
    logging.basicConfig(
        level=settings.loglevel,
        format="%(asctime)s pid:%(process)d %(threadName)s %(name)-12s %(levelname)-8s %(message)s",
        handlers=[stdout_handler],
    )


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
            logger.error("Timer was not started")
            return

        self.duration = timedelta(seconds=default_timer() - self.__start_time)
        if log:
            self.message = self.create_message(self.duration)
            logger.log(self.level, self.message)
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
    @wraps(timer)
    def timing_decorator(fn):
        @wraps(timing_decorator)
        def wrap(*args, **kw):
            with Timer(message if message else f"{fn.__module__}.{fn.__qualname__}"):
                result = fn(*args, **kw)
            return result

        return wrap

    return timing_decorator
