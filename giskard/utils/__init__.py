import logging
import os
from concurrent.futures import Future
from functools import wraps
from threading import Lock, Thread
from time import sleep

from giskard.settings import settings
from giskard.utils.worker_pool import WorkerPoolExecutor

LOGGER = logging.getLogger(__name__)


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, daemon=True, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


NOT_STARTED = "Pool is not started"


class SingletonWorkerPool:
    "Utility class to wrap a Process pool"

    def __init__(self):
        self.pool = None
        self.max_workers = 0

    def start(self, max_workers: int = None):
        if self.pool is not None:
            return
        self.max_workers = max(max_workers, settings.min_workers) if max_workers is not None else os.cpu_count()
        self.pool = WorkerPoolExecutor(nb_workers=self.max_workers)

    def shutdown(self, wait=True):
        if self.pool is None:
            return
        self.pool.shutdown(wait=wait)

    def schedule(self, fn, args=None, kwargs=None, timeout=None) -> Future:
        if self.pool is None:
            raise RuntimeError(NOT_STARTED)
        return self.pool.schedule(fn, args=args, kwargs=kwargs, timeout=timeout)

    def submit(self, *args, **kwargs) -> Future:
        if self.pool is None:
            raise RuntimeError(NOT_STARTED)
        return self.pool.submit(*args, **kwargs)

    def map(self, *args, **kwargs):
        if self.pool is None:
            raise RuntimeError(NOT_STARTED)
        return self.pool.map(*args, **kwargs)


POOL = SingletonWorkerPool()


def start_pool(max_workers: int = None):
    """Start the pool and warm it up, to get all workers up.

    Args:
        max_workers (int, optional): _description_. Defaults to None.
    """
    if not settings.use_pool:
        LOGGER.warning("Execution in pool is disabled, this should only happen for test and debug")
        return
    POOL.start(max_workers=max_workers)
    # Warmup the pool
    for _ in range(100):
        call_in_pool(sleep, [0])


def shutdown_pool():
    """Stop the pool"""
    if not settings.use_pool:
        LOGGER.warning("Execution in pool is disabled, this should only happen for test and debug")
        return

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
