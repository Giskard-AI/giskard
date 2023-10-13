from multiprocessing.context import SpawnProcess
from time import sleep

import pytest

from giskard.utils.worker_pool import WorkerPoolExecutor


@pytest.fixture(scope="function")
def many_worker_pool():
    pool = WorkerPoolExecutor(nb_workers=4)
    sleep(3)
    yield pool
    pool.shutdown(wait=True)


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
    exit_codes = pool.shutdown(wait=True)
    assert exit_codes == [0]


def add_one(elt):
    return elt + 1


def sleep_add_one(timer, value):
    sleep(timer)
    return value + 1


@pytest.mark.concurrency
def test_submit_one_task(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.submit(add_one, 1)
    assert future.result(timeout=5) == 2


@pytest.mark.concurrency
def test_task_should_be_cancelled(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.schedule(sleep_add_one, [1000, 1], timeout=1)
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
        assert "Task took too long" in str(exc_info)


@pytest.mark.concurrency
def test_after_cancel_should_work(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.schedule(sleep_add_one, [100, 1], timeout=1)
    pid = set(one_worker_pool._running_process.keys())
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
        assert "Task took too long" in str(exc_info)
    new_pid = set(one_worker_pool._running_process.keys())
    assert pid != new_pid
    future = one_worker_pool.schedule(sleep_add_one, [2, 2], timeout=10)
    assert future.result() == 3
    future = one_worker_pool.schedule(add_one, [2])
    assert future.result() == 3
    future = one_worker_pool.submit(add_one, 4)
    assert future.result() == 5


@pytest.mark.concurrency
def test_after_cancel_should_shutdown_nicely():
    one_worker_pool = WorkerPoolExecutor(nb_workers=1)
    sleep(3)
    future = one_worker_pool.schedule(sleep_add_one, [100, 1], timeout=1)
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
    exit_codes = one_worker_pool.shutdown(wait=True)
    assert exit_codes == [0]


@pytest.mark.concurrency
def test_many_tasks_should_shutdown_nicely():
    one_worker_pool = WorkerPoolExecutor(nb_workers=4)
    sleep(3)
    for _ in range(100):
        one_worker_pool.schedule(sleep_add_one, [2, 2], timeout=5)
    sleep(3)
    worker_process: SpawnProcess = list(one_worker_pool._processes.values())[0]
    assert worker_process.is_alive()
    exit_codes = one_worker_pool.shutdown(wait=True)
    print(exit_codes)
    assert all([code is not None for code in exit_codes])


@pytest.mark.concurrency
def test_submit_many_task(many_worker_pool: WorkerPoolExecutor):
    futures = []
    for i in range(100):
        futures.append(many_worker_pool.schedule(sleep_add_one, [0.1, i], timeout=20))
    for i in range(100, 200):
        futures.append(many_worker_pool.submit(add_one, i))

    for expected, future in enumerate(futures):
        assert expected + 1 == future.result()
