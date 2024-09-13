import logging
from threading import Thread

LOGGER = logging.getLogger(__name__)


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, daemon=True, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == "__builtin__":
        return klass.__name__
    return module + "." + klass.__name__
