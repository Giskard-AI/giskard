from typing import Any, Callable, Dict, List, Optional, Tuple

import logging
import os
import time
from concurrent.futures import Executor, Future
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing import Queue, SimpleQueue, cpu_count, get_context
from multiprocessing.context import SpawnContext, SpawnProcess
from multiprocessing.managers import SyncManager
from threading import Thread
from time import sleep
from uuid import uuid4

LOGGER = logging.getLogger(__name__)


def _generate_task_id():
    return str(uuid4())


@dataclass
class TimeoutData:
    id: str
    end_time: float


@dataclass
class GiskardTask:
    callable: Callable
    args: Any
    kwargs: Any
    id: str = field(default_factory=_generate_task_id)


@dataclass
class GiskardResult:
    id: str
    result: Any = None
    exception: Any = None


def _process_worker(tasks_queue: SimpleQueue, tasks_results: SimpleQueue, running_process: Dict[str, str]):
    # TODO(Bazire): For now, worker stops because the queues will be closed. Not the cleanest...
    pid = os.getpid()

    while True:
        # Blocking accessor, will wait for a task
        task: GiskardTask = tasks_queue.get()
        if task is None:
            return
        try:
            LOGGER.debug("Doing task %", task.id)
            running_process[task.id] = pid
            result = task.callable(*task.args, **task.kwargs)
            to_return = GiskardResult(id=task.id, result=result)
        except BaseException as e:
            to_return = GiskardResult(id=task.id, exception=str(e))
        finally:
            running_process.pop(task.id)
            tasks_results.put(to_return)


# Note: See _on_queue_feeder_error
class PoolState(Enum):
    STARTING = 0
    STARTED = 1
    BROKEN = 2
    STOPPING = 3
    STOPPED = 4


FINAL_STATES = [PoolState.STOPPING, PoolState.STOPPED, PoolState.BROKEN]


class WorkerPoolExecutor(Executor):
    def __init__(self, nb_workers: Optional[int] = None):
        if nb_workers is None:
            nb_workers = cpu_count()
        if nb_workers <= 0:
            raise ValueError("nb_workers should be strictly positive (or None)")
        self._nb_workers = nb_workers
        self._state = PoolState.STARTING
        # Forcing spawn context, to have same behaviour between all os
        self._mp_context: SpawnContext = get_context("spawn")
        # Map of pids to processes
        self._processes: Dict[int, SpawnProcess] = {}
        # Manager to handle shared object
        self._manager: SyncManager = self._mp_context.Manager()
        # Mapping of the running tasks and worker pids
        self._running_process: Dict[str, str] = self._manager.dict()
        # Mapping of the running tasks and worker pids
        self._with_timeout_tasks: List[Tuple[str, float]] = []
        # Queue with tasks to run
        self._pending_tasks_queue: SimpleQueue[GiskardTask] = self._mp_context.SimpleQueue()
        # Queue with tasks to run
        # As in ProcessPool, add one more to avoid idling process
        self._running_tasks_queue: Queue[GiskardTask] = self._mp_context.Queue(maxsize=self._nb_workers + 1)
        # Queue with results to notify
        self._tasks_results: SimpleQueue[GiskardResult] = self._mp_context.SimpleQueue()
        # Mapping task_id with future
        self._futures_mapping: Dict[str, Future] = dict()

        self._threads = [
            Thread(name="giskard_pool_" + target.__name__, target=target, daemon=True, args=[self], kwargs=None)
            for target in [_killer_thread, _feeder_thread, _results_thread]
        ]
        for t in self._threads:
            t.start()

        # Startup workers
        for _ in range(self._nb_workers):
            self._spawn_worker()

    def _spawn_worker(self):
        # Daemon means process are linked to main one, and will be stopped if current process is stopped
        p = self._mp_context.Process(
            target=_process_worker,
            name="giskard_worker_process",
            args=(self._running_tasks_queue, self._tasks_results, self._running_process),
            daemon=True,
        )
        p.start()
        self._processes[p.pid] = p
        LOGGER.info("Starting a new worker %s", p.pid)

    def submit(self, fn, *args, **kwargs):
        return self.schedule(fn, args=args, kwargs=kwargs, timeout=None)

    def schedule(
        self,
        fn,
        args=None,
        kwargs=None,
        timeout: Optional[float] = None,
    ):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if self._state in FINAL_STATES:
            raise RuntimeError(f"Cannot submit when pool is {self._state.name}")
        task = GiskardTask(callable=fn, args=args, kwargs=kwargs)
        res = Future()
        self._futures_mapping[task.id] = res
        self._pending_tasks_queue.put(task)
        if timeout is not None:
            self._with_timeout_tasks.append((task.id, time.monotonic() + timeout))
        return res

    def shutdown(self, wait=True, timeout: float = 5):
        if self._state in FINAL_STATES:
            return
        # Changing state, so that thread will stop
        # Killer thread will also do cleanup
        self._state = PoolState.STOPPING
        # Cancelling all futures we have
        for future in self._futures_mapping.values():
            future.cancel()
        # Closing the queue will actually stop the workers
        while not self._running_tasks_queue.empty():
            try:
                self._running_tasks_queue.get_nowait()
            except BaseException:
                pass
        # Try to nicely stop the worker
        for _ in range(self._nb_workers):
            self._running_tasks_queue.put(None, timeout=1)
        if wait:
            end_time = time.monotonic() + timeout
            while time.monotonic() < end_time:
                if all([not p.is_alive() for p in self._processes.values()]):
                    break
                sleep(0.1)
        self._pending_tasks_queue.close()
        self._tasks_results.close()
        self._running_tasks_queue.close()
        # Waiting for threads to finish
        for t in self._threads:
            t.join(timeout=1)
            if t.is_alive():
                LOGGER.warning("Thread %s still alive at shutdown", t.name)
        # Changing state to stopped
        self._state = PoolState.STOPPED
        # Cleaning up processes
        for p in self._processes.values():
            if p.exitcode is None:
                LOGGER.warning("Some process was still running, killing it")
                p.kill()
        self._manager.shutdown()


def _results_thread(
    executor: WorkerPoolExecutor,
):
    # Goal of this thread is to feed the running tasks from pending one as soon as possible
    while True:
        while executor._state not in FINAL_STATES and (executor._tasks_results.empty()):
            # TODO(Bazire): find a way to improve this ?
            # Cannot use select, since we want to be windows compatible
            sleep(0.01)
        if executor._state in FINAL_STATES:
            return
        result = executor._tasks_results.get()
        future = executor._futures_mapping.get(result.id)
        if future.cancelled():
            try:
                del executor._futures_mapping[result.id]
            except BaseException:
                pass
            continue
        if result.result is not None:
            future.set_result(result.result)
        else:
            # TODO(Bazire): improve to get Traceback
            future.set_exception(RuntimeError(result.exception))
        try:
            del executor._futures_mapping[result.id]
        except BaseException:
            pass


def _feeder_thread(
    executor: WorkerPoolExecutor,
):
    # Goal of this thread is to feed the running tasks from pending one as soon as possible
    while True:
        while executor._state not in FINAL_STATES and (
            executor._running_tasks_queue.full() or executor._pending_tasks_queue.empty()
        ):
            # TODO(Bazire): find a way to improve this ?
            # Cannot use select, since we want to be windows compatible
            sleep(0.01)
        if executor._state in FINAL_STATES:
            return
        task = executor._pending_tasks_queue.get()
        future = executor._futures_mapping.get(task.id)
        if future is not None and future.set_running_or_notify_cancel():
            executor._running_tasks_queue.put(task)
        elif future is not None:
            # Future has been cancelled already, nothing to do
            del executor._futures_mapping[task.id]


def _killer_thread(
    executor: WorkerPoolExecutor,
):
    while True:
        while len(executor._with_timeout_tasks) == 0 and executor._state not in FINAL_STATES:
            # No need to be too active
            sleep(1)
        if executor._state in FINAL_STATES:
            return

        clean_up = []
        exception = None
        for timeout_data in executor._with_timeout_tasks:
            task_id, end_time = timeout_data
            if task_id not in executor._futures_mapping:
                # Task is already completed, do not wait for it
                clean_up.append(timeout_data)
            elif time.monotonic() > end_time:
                # Task has timed out, we should kill it
                try:
                    pid = executor._running_process.get(task_id)
                    if pid is None:
                        # Task must have finished
                        continue
                    future = executor._futures_mapping.get(task_id)
                    if not future.cancel():
                        LOGGER.warning("Killing a timed out process")
                        future.set_exception(TimeoutError("Task took too long"))
                        executor._processes[pid].kill()
                        del executor._processes[pid]
                        executor._spawn_worker()
                except BaseException as e:
                    LOGGER.warning("Unexpected error when killing a timed out process, pool is broken")
                    LOGGER.exception(e)
                    exception = e
                    executor._state = PoolState.BROKEN
                finally:
                    clean_up.append(timeout_data)
        for elt in clean_up:
            executor._with_timeout_tasks.remove(elt)

        if exception is not None:
            raise exception

        if executor._state in FINAL_STATES:
            return


def add(a):
    sleep(a / 10)
    return a + 1


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    import concurrent.futures

    pool = WorkerPoolExecutor(nb_workers=None)
    sleep(3)
    results = []

    for i in range(50):
        results.append(pool.schedule(add, [i], {}, timeout=2))

    done, _ = concurrent.futures.wait(results, return_when="ALL_COMPLETED", timeout=60)
    # assert len(done) == len(results)
    values = [f.result() for f in results if f.exception() is None]
    # result = pool.map(add, range(1000))
    print(values)
    print([p.exitcode for p in pool._processes.values()])
    pool.shutdown()
