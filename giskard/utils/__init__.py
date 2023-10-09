import logging
from asyncio import Future
from concurrent.futures import ProcessPoolExecutor
from functools import wraps
from threading import Thread

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

    def start(self, *args, **kwargs):
        if self.pool is not None:
            return
        LOGGER.info("Starting worker pool...")
        self.pool = ProcessPoolExecutor(*args, **kwargs)
        LOGGER.info("Pool is started")

    def shutdown(self, wait=True, cancel_futures=False):
        if self.pool is None:
            return
        self.pool.shutdown(wait=wait, cancel_futures=cancel_futures)
        self.pool = None

    def submit(self, *args, **kwargs) -> Future:
        if self.pool is None:
            raise ValueError("Pool is not started")
        return self.pool.submit(*args, **kwargs)

    def map(self, *args, **kwargs):
        if self.pool is None:
            raise ValueError("Pool is not started")
        return self.pool.map(*args, **kwargs)

    def log_stats(self):
        if self.pool is None:
            LOGGER.debug("Pool is not yet started")
        LOGGER.debug(
            "Pool is currently having :\n - %s pending items\n - %s workers",
            len(self.pool._pending_work_items),
            len(self.pool._processes),
        )


POOL = WorkerPool()


def log_pool_stats():
    """Log pools stats to have some debug info"""
    POOL.log_stats()


def start_pool(max_workers: int = None):
    """Start the pool and warm it up, to get all workers up.

    Args:
        max_workers (int, optional): _description_. Defaults to None.
    """
    POOL.start(max_workers=max_workers)
    # Doing warmup to spin up all workers
    for _ in POOL.map(int, range(100)):
        # Consume the results
        pass
    log_pool_stats()


def shutdown_pool():
    """Stop the pool"""
    POOL.shutdown(wait=True, cancel_futures=True)


def call_in_pool(fn, *args, **kwargs):
    """Submit the function call with args and kwargs inside the process pool

    Args:
        fn (function): the function to call

    Returns:
        Future: the promise of the results
    """
    return POOL.submit(fn, *args, **kwargs)


def pooled(fn):
    """Decorator to make a function be called inside the pool.

    Args:
        fn (function): the function to wrap
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return call_in_pool(fn, *args, **kwargs)

    return wrapper


def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == "__builtin__":
        return klass.__name__
    return module + "." + klass.__name__
