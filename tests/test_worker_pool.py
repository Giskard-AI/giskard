import logging
from multiprocessing.context import SpawnProcess
from time import sleep

import pytest

from giskard.utils.worker_pool import WorkerPoolExecutor

logging.basicConfig(level="debug")


@pytest.fixture(scope="function")
def one_worker_pool():
    pool = WorkerPoolExecutor(nb_workers=1)
    sleep(3)
    yield pool
    pool.shutdown(wait=True)


@pytest.mark.concurrency
def test_start_stop():
    pool = WorkerPoolExecutor(nb_workers=1)
    assert len(pool._processes) == 1
    worker_process: SpawnProcess = list(pool._processes.values())[0]
    assert worker_process.is_alive()
    pool.shutdown(wait=True)
    assert not worker_process.is_alive()
    assert worker_process.exitcode == 0


def add_one(elt):
    return elt + 1


def sleep_add_one(timer):
    sleep(timer)
    return timer + 1


@pytest.mark.concurrency
def test_submit_one_task(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.submit(add_one, 1)
    assert future.result(timeout=5) == 2


@pytest.mark.concurrency
def test_task_should_be_cancelled(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.schedule(sleep_add_one, [1000], timeout=1)
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
        assert "Task took too long" in str(exc_info)


@pytest.mark.concurrency
def test_after_cancel_should_work(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.schedule(sleep_add_one, [100], timeout=1)
    pid = set(one_worker_pool._running_process.keys())
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
        assert "Task took too long" in str(exc_info)
    new_pid = set(one_worker_pool._running_process.keys())
    assert pid != new_pid
    future = one_worker_pool.schedule(sleep_add_one, [2], timeout=10)
    assert future.result() == 3
    future = one_worker_pool.schedule(add_one, [2])
    assert future.result() == 3
    future = one_worker_pool.submit(add_one, 4)
    assert future.result() == 5


@pytest.mark.concurrency
def test_after_cancel_should_shutdown_nicely():
    one_worker_pool = WorkerPoolExecutor(nb_workers=1)
    sleep(3)
    future = one_worker_pool.schedule(sleep_add_one, [100], timeout=1)
    pid = set(one_worker_pool._running_process.keys())
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
        assert "Task took too long" in str(exc_info)
    new_pid = set(one_worker_pool._running_process.keys())
    assert pid != new_pid
    future = one_worker_pool.submit(add_one, 4)
    assert future.result() == 5
    assert len(one_worker_pool._processes) == 1
    worker_process: SpawnProcess = list(one_worker_pool._processes.values())[0]
    assert worker_process.is_alive()
    one_worker_pool.shutdown(wait=True)
    assert not worker_process.is_alive()
    assert worker_process.exitcode == 0
