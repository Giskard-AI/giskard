import logging
import os
from concurrent.futures import Future
from functools import wraps
from threading import Lock, Thread

from giskard.settings import settings
from giskard.utils.worker_pool import WorkerPoolExecutor

LOGGER = logging.getLogger(__name__)


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class WorkerPool:
    "Utility class to wrap a Process pool"

    def __init__(self):
        self.pool = None
        self.max_workers = 0

    def start(self, max_workers: int = None):
        if self.pool is not None:
            return
        self.max_workers = max(max_workers, settings.min_workers) if max_workers is not None else os.cpu_count()
        LOGGER.info("Starting worker pool with %s workers...", self.max_workers)
        self.pool = WorkerPoolExecutor(nb_workers=self.max_workers)
        LOGGER.info("Pool is started")

    def shutdown(self, wait=True):
        if self.pool is None:
            return
        self.pool.shutdown(wait=wait)

    def schedule(self, fn, args=None, kwargs=None, timeout=None) -> Future:
        if self.pool is None:
            raise ValueError("Pool is not started")
        return self.pool.schedule(fn, args=args, kwargs=kwargs, timeout=timeout)

    def submit(self, *args, **kwargs) -> Future:
        if self.pool is None:
            raise ValueError("Pool is not started")
        return self.pool.submit(*args, **kwargs)

    def map(self, *args, **kwargs):
        if self.pool is None:
            raise ValueError("Pool is not started")
        return self.pool.map(*args, **kwargs)


POOL = WorkerPool()


def start_pool(max_workers: int = None):
    """Start the pool and warm it up, to get all workers up.

    Args:
        max_workers (int, optional): _description_. Defaults to None.
    """
    POOL.start(max_workers=max_workers)


def shutdown_pool():
    """Stop the pool"""
    POOL.shutdown(wait=True)


def pooled(fn):
    """Decorator to make a function be called inside the pool.

    Args:
        fn (function): the function to wrap
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return call_in_pool(fn, args=args, kwargs=kwargs)

    return wrapper


NB_CANCELLABLE_WORKER_LOCK = Lock()


def call_in_pool(
    fn,
    args=None,
    kwargs=None,
    timeout=None,
):
    return POOL.schedule(fn, args=args, kwargs=kwargs, timeout=timeout)


def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == "__builtin__":
        return klass.__name__
    return module + "." + klass.__name__
