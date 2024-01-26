import logging
import os
from concurrent.futures import Future
from threading import Thread
from uuid import UUID

from giskard.settings import settings
from giskard.utils.worker_pool import KillReason, WorkerPoolExecutor

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

    def cancel(self, job_id: UUID):
        self.pool.kill_task(job_id, KillReason.CANCELLED)

    def shutdown(self, wait=True):
        if self.pool is None:
            return
        self.pool.shutdown(wait=wait)

    def schedule(self, job_id: UUID, fn, args=None, kwargs=None, timeout=None) -> Future:
        if self.pool is None:
            raise RuntimeError(NOT_STARTED)
        return self.pool.schedule(job_id, fn, args=args, kwargs=kwargs, timeout=timeout)

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
        max_workers (Optional[int]): _description_. Defaults to None.
    """
    if not settings.use_pool:
        LOGGER.warning("Execution in pool is disabled, this should only happen for test and debug")
        return
    POOL.start(max_workers=max_workers)


def shutdown_pool():
    """Stop the pool"""
    if not settings.use_pool:
        LOGGER.warning("Execution in pool is disabled, this should only happen for test and debug")
        return

    POOL.shutdown(wait=True)


def call_in_pool(
    job_id: UUID,
    fn,
    args=None,
    kwargs=None,
    timeout=None,
):
    return POOL.schedule(job_id, fn, args=args, kwargs=kwargs, timeout=timeout)


def cancel_in_pool(job_id: UUID):
    POOL.cancel(job_id)


def list_pool_job_ids():
    if POOL.pool:
        return list(POOL.pool.futures_mapping.keys())
    else:
        return []


def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == "__builtin__":
        return klass.__name__
    return module + "." + klass.__name__
