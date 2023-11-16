import logging
import sys
import tempfile
from multiprocessing.context import SpawnProcess
from pathlib import Path
from time import sleep
from uuid import uuid4

import pytest

from giskard.utils.worker_pool import GiskardMLWorkerException, PoolState, WorkerPoolExecutor


@pytest.fixture(scope="function")
def many_worker_pool():
    pool = WorkerPoolExecutor(nb_workers=4)
    sleep(5)
    yield pool
    pool.shutdown(wait=True, timeout=60)
    pool.shutdown(wait=True, force=True, timeout=60)


@pytest.fixture(scope="function")
def one_worker_pool():
    pool = WorkerPoolExecutor(nb_workers=1)
    sleep(5)
    yield pool
    pool.shutdown(wait=True, timeout=2)
    pool.shutdown(wait=True, force=True, timeout=10)


@pytest.mark.concurrency
def test_start_stop():
    pool = WorkerPoolExecutor(nb_workers=1)
    assert len(pool.processes) == 1
    worker_process: SpawnProcess = list(pool.processes.values())[0]
    assert worker_process.is_alive()
    exit_codes = pool.shutdown(wait=True, timeout=10)
    assert exit_codes == [0]


@pytest.mark.concurrency
def test_force_stopping_should_always_succeed():
    pool = WorkerPoolExecutor(nb_workers=1)
    assert len(pool.processes) == 1
    worker_process: SpawnProcess = list(pool.processes.values())[0]
    assert worker_process.is_alive()
    exit_codes = pool.shutdown(wait=True, timeout=10)
    assert exit_codes == [0]
    pool.shutdown(wait=False, force=True)


def create_file(path: Path):
    return path.touch()


def add_one(elt):
    return elt + 1


def sleep_add_one(timer, value):
    sleep(timer)
    return value + 1


def print_stuff():
    print("stuff stdout")
    print("other stuff", file=sys.stderr)
    logging.getLogger().info("info log")
    logging.getLogger("truc").error("toto")
    logging.getLogger(__name__).warning("Warning")
    return


def bugged_code():
    print("Before raising")
    return 1 / 0


@pytest.mark.concurrency
def test_handle_log(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.submit(print_stuff)
    assert future.result(timeout=5) is None
    print(future.logs)
    assert "stuff stdout" in future.logs
    assert "other stuff" in future.logs
    assert "info log" in future.logs
    assert "toto" in future.logs
    assert "Warning" in future.logs


@pytest.mark.concurrency
def test_handle_exception_log(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.submit(bugged_code)
    exception = future.exception(timeout=5)
    assert exception is not None
    print(exception)
    assert isinstance(exception, GiskardMLWorkerException)
    stacktrace = exception.info.stack_trace
    assert "ZeroDivisionError: division by zero" in stacktrace
    assert "in bugged_code" in stacktrace
    assert "return 1 / 0" in stacktrace
    print(future.logs)
    assert "Before raising" in future.logs
    assert "ZeroDivisionError: division by zero" in future.logs
    assert "in bugged_code" in future.logs
    assert "return 1 / 0" in future.logs
    assert len(one_worker_pool.futures_mapping) == 0


@pytest.mark.concurrency
def test_submit_one_task(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.submit(add_one, 1)
    assert future.result(timeout=5) == 2
    assert len(one_worker_pool.futures_mapping) == 0


@pytest.mark.concurrency
def test_task_should_be_cancelled(one_worker_pool: WorkerPoolExecutor):
    future = one_worker_pool.schedule(sleep_add_one, [180, 1], timeout=1)
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
    assert "Task took too long" in str(exc_info)
    assert len(one_worker_pool.futures_mapping) == 0


@pytest.mark.concurrency
def test_after_cancel_should_work(one_worker_pool: WorkerPoolExecutor):
    pid = set(one_worker_pool.processes.keys())
    assert len(pid) == 1
    future = one_worker_pool.schedule(sleep_add_one, [100, 1], timeout=10)
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
    assert "Task took too long" in str(exc_info)
    sleep(8)
    new_pid = set(one_worker_pool.processes.keys())
    assert len(new_pid) == 1
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
    pid = set(one_worker_pool.processes.keys())
    future = one_worker_pool.schedule(sleep_add_one, [100, 1], timeout=10)
    sleep(3)
    with pytest.raises(TimeoutError) as exc_info:
        future.result()
    assert "Task took too long" in str(exc_info)
    sleep(8)
    new_pid = set(one_worker_pool.processes.keys())
    assert pid != new_pid
    future = one_worker_pool.submit(add_one, 4)
    assert future.result() == 5
    assert len(one_worker_pool.processes) == 1
    worker_process: SpawnProcess = list(one_worker_pool.processes.values())[0]
    assert worker_process.is_alive()
    exit_codes = one_worker_pool.shutdown(wait=True)
    assert exit_codes == [0]


@pytest.mark.skipif(condition=sys.platform == "win32", reason="Not working on windows")
@pytest.mark.concurrency
def test_many_tasks_should_shutdown_nicely(many_worker_pool: WorkerPoolExecutor):
    sleep(3)
    futures = []
    for _ in range(100):
        futures.append(many_worker_pool.schedule(sleep_add_one, [2, 2], timeout=20))
    sleep(30)
    exit_codes = many_worker_pool.shutdown(wait=True, timeout=60)
    assert len([code is not None for code in exit_codes]) == 4
    assert all([code is not None for code in exit_codes])
    assert exit_codes == [0, 0, 0, 0]
    assert all([f.done() for f in futures])
    assert all([not t.is_alive() for t in many_worker_pool._threads])


@pytest.mark.concurrency
def test_many_tasks_shutdown_while_running(one_worker_pool: WorkerPoolExecutor):
    sleep(3)
    futures = []
    for _ in range(1):
        futures.append(one_worker_pool.schedule(sleep_add_one, [10, 2], timeout=20))
    sleep(1)
    exit_codes = one_worker_pool.shutdown(wait=True, timeout=60)
    assert len([code is not None for code in exit_codes]) == 1
    assert all([not t.is_alive() for t in one_worker_pool._threads])
    sleep(5)
    assert sum([0 if f.done() else 1 for f in futures]) == 0


@pytest.mark.concurrency
def test_submit_many_task(many_worker_pool: WorkerPoolExecutor):
    futures = []
    for i in range(100):
        futures.append(many_worker_pool.schedule(sleep_add_one, [0.1, i], timeout=20))
    for i in range(100, 200):
        futures.append(many_worker_pool.submit(add_one, i))

    for expected, future in enumerate(futures):
        assert expected + 1 == future.result()


@pytest.mark.concurrency
def test_task_already_cancelled(one_worker_pool: WorkerPoolExecutor):
    for _ in range(10):
        # Saturate the pool with tasks
        one_worker_pool.schedule(sleep_add_one, [180, 1], timeout=3)
    # Schedule an easy task
    temp_path = Path(tempfile.gettempdir()) / str(uuid4())
    temp_path.touch()
    assert temp_path.exists()  # Ensure there is no access right issues
    temp_path.unlink()
    # Make sure file does not exist
    assert not temp_path.exists()
    future = one_worker_pool.submit(create_file, temp_path)
    task_id = [k for k, v in one_worker_pool.futures_mapping.items() if v == future][0]
    assert task_id is not None
    # Cancel it
    assert future.cancel()
    assert future.done()
    # Wait a bit
    sleep(20)
    # Ensure task has not been executed
    assert not temp_path.exists()
    # Ensure future is not there anymore
    assert task_id not in one_worker_pool.futures_mapping.keys()


@pytest.mark.concurrency
def test_pool_should_break(one_worker_pool: WorkerPoolExecutor):
    process = list(one_worker_pool.processes.values())[0]
    process.kill()
    sleep(2)
    assert one_worker_pool._state == PoolState.BROKEN
    with pytest.raises(RuntimeError) as exc_info:
        one_worker_pool.schedule(sleep_add_one, [180, 1], timeout=1)
    assert "Cannot submit when pool is BROKEN" in str(exc_info)
