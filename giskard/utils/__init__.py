import logging
import os
import signal
from concurrent.futures import CancelledError, Future, InvalidStateError, ProcessPoolExecutor
from functools import wraps
from threading import Lock, Thread
from time import sleep, time

from giskard.settings import settings

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
        self.nb_cancellable = 0
        self.max_workers = 0

    def start(self, max_workers: int = None):
        if self.pool is not None:
            return
        self.max_workers = max(max_workers, settings.min_workers) if max_workers is not None else os.cpu_count()
        LOGGER.info("Starting worker pool with %s workers...", self.max_workers)
        self.pool = ProcessPoolExecutor(max_workers=self.max_workers)
        LOGGER.info("Pool is started")

    def shutdown(self, wait=True, cancel_futures=False):
        if self.pool is None:
            return
        self.pool.shutdown(wait=wait, cancel_futures=cancel_futures)
        with NB_CANCELLABLE_WORKER_LOCK:
            self.nb_cancellable = 0

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
            return
        LOGGER.debug(
            "Pool is currently having :\n - %s pending items\n - %s workers\n - %s cancellable tasks",
            len(self.pool._pending_work_items),
            len(self.pool._processes),
            self.nb_cancellable,
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


def pooled(fn):
    """Decorator to make a function be called inside the pool.

    Args:
        fn (function): the function to wrap
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return call_in_pool(fn, *args, **kwargs)

    return wrapper


NB_CANCELLABLE_WORKER_LOCK = Lock()


@threaded
def start_killer(timeout: float, future: Future, pid: int, executor: ProcessPoolExecutor):
    start = time()
    # Try to get the result in proper time
    while (time() - start) < timeout:
        # future.result(timeout=timeout) => Not working with WSL and python 3.10, switchin to something safer
        LOGGER.debug("Sleeping for pid %s", pid)
        sleep(1)
        if future.done():
            executor.shutdown(wait=True, cancel_futures=False)
            with NB_CANCELLABLE_WORKER_LOCK:
                POOL.nb_cancellable -= 1
            return
    LOGGER.warning("Thread gonna kill pid %s", pid)
    # Manually setting exception, to allow customisation
    # TODO(Bazire): See if we need a custom error to handle that properly
    try:
        future.set_exception(CancelledError("Background task was taking too much time and was cancelled"))
    except InvalidStateError:
        pass
    # Shutting down an executor is actually not stopping the running processes
    executor.shutdown(wait=False, cancel_futures=False)
    # Kill the process running by targeting its pid
    os.kill(pid, signal.SIGINT)
    # Let's clean up the executor also
    # Also, does not matter to call shutdown several times
    executor.shutdown(wait=True, cancel_futures=False)
    with NB_CANCELLABLE_WORKER_LOCK:
        POOL.nb_cancellable -= 1
    LOGGER.debug("Executor has been successfully shutdown")
    log_pool_stats()


def call_in_pool(fn, *args, timeout=None, **kwargs):
    """Submit the function call with args and kwargs inside the process pool

    Args:
        fn (function): the function to call

    Returns:
        Future: the promise of the results
    """
    if timeout is None:
        return POOL.submit(fn, *args, **kwargs)
    # Create independant process pool
    # If we kill a running process, it breaking the Process pool, making it unusable
    one_shot_executor = ProcessPoolExecutor(max_workers=1)
    pid = one_shot_executor.submit(os.getpid).result(timeout=5)
    future = one_shot_executor.submit(fn, *args, **kwargs)
    start_killer(timeout, future, pid, one_shot_executor)
    with NB_CANCELLABLE_WORKER_LOCK:
        POOL.nb_cancellable += 1
    return future


def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == "__builtin__":
        return klass.__name__
    return module + "." + klass.__name__
