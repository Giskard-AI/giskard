from typing import Any, Callable, Dict, List, Optional, Tuple

import logging
import os
import time
import traceback
from concurrent.futures import CancelledError, Executor, Future
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from enum import Enum
from io import StringIO
from multiprocessing import Process, Queue, SimpleQueue, cpu_count, get_context
from multiprocessing.context import SpawnContext, SpawnProcess
from multiprocessing.managers import SyncManager
from queue import Empty
from threading import Thread
from time import sleep
from uuid import uuid4

LOGGER = logging.getLogger(__name__)


def _generate_task_id():
    return str(uuid4())


def _safe_is_alive(p: Process) -> bool:
    try:
        return p.is_alive()
    except ValueError:
        return False


def _safe_exit_code(p: Process) -> int:
    try:
        return p.exitcode
    except ValueError:
        return -1


def _wait_process_stop(p_list: List[Process], timeout: float = 1):
    end_time = time.monotonic() + timeout
    while any([_safe_is_alive(p) for p in p_list]) and time.monotonic() < end_time:
        sleep(0.1)


def _stop_processes(p_list: List[Process], timeout: float = 1) -> List[Optional[int]]:
    # Check if process is alive.
    for p in p_list:
        if _safe_is_alive(p):
            # Try to terminate with SIGTERM first
            p.terminate()
    _wait_process_stop(p_list, timeout=timeout)

    for p in p_list:
        if _safe_is_alive(p):
            # If still alive, kill the processes
            p.kill()
    _wait_process_stop(p_list, timeout=2)
    exit_codes = [_safe_exit_code(p) for p in p_list]
    # Free all resources
    for p in p_list:
        p.close()
    return exit_codes


class GiskardFuture(Future):
    def __init__(self) -> None:
        super().__init__()
        self.logs = ""


@dataclass(frozen=True)
class TimeoutData:
    id: str
    end_time: float


@dataclass(frozen=True)
class GiskardTask:
    callable: Callable
    args: Any
    kwargs: Any
    id: str = field(default_factory=_generate_task_id)


@dataclass(frozen=True)
class GiskardResult:
    id: str
    logs: str
    result: Any = None
    exception: Any = None


def _process_worker(tasks_queue: SimpleQueue, tasks_results: SimpleQueue, running_process: Dict[str, str]):
    pid = os.getpid()

    while True:
        # Blocking accessor, will wait for a task
        task: GiskardTask = tasks_queue.get()
        # This is how we cleanly stop the workers
        if task is None:
            return
        # Capture any log (stdout, stderr + root logger)
        with redirect_stdout(StringIO()) as f:
            with redirect_stderr(f):
                handler = logging.StreamHandler(f)
                logging.getLogger().addHandler(handler)
                try:
                    LOGGER.debug("Doing task %s", task.id)
                    running_process[task.id] = pid
                    result = task.callable(*task.args, **task.kwargs)
                    to_return = GiskardResult(id=task.id, result=result, logs=f.getvalue())
                except BaseException as e:
                    exception = "\n".join(traceback.format_exception(type(e), e, e.__traceback__))
                    to_return = GiskardResult(id=task.id, exception=exception, logs=f.getvalue() + "\n" + exception)
                finally:
                    running_process.pop(task.id)
                    tasks_results.put(to_return)
                    logging.getLogger().removeHandler(handler)


# Note: See _on_queue_feeder_error
class PoolState(Enum):
    STARTING = 0
    STARTED = 1
    BROKEN = 2
    STOPPING = 3
    STOPPED = 4


FINAL_STATES = [PoolState.STOPPING, PoolState.STOPPED, PoolState.BROKEN]


class WorkerPoolExecutor(Executor):
    def __init__(self, nb_workers: Optional[int] = None, name: Optional[str] = None):
        self._prefix = f"{name}_" if name is not None else "giskard_pool_"
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
        self._with_timeout_tasks: List[TimeoutData] = []
        # Queue with tasks to run
        self._pending_tasks_queue: Queue[GiskardTask] = self._mp_context.Queue()
        # Queue with tasks to be consumed asap
        # As in ProcessPool, add one more to avoid idling process
        self._running_tasks_queue: Queue[Optional[GiskardTask]] = self._mp_context.Queue(maxsize=self._nb_workers + 1)
        # Queue with results to notify
        self._tasks_results: Queue[GiskardResult] = self._mp_context.Queue()
        # Mapping task_id with future
        self._futures_mapping: Dict[str, Future] = dict()
        LOGGER.debug("Starting threads for the WorkerPoolExecutor")

        self._threads = [
            Thread(name=f"{self._prefix}{target.__name__}", target=target, daemon=True, args=[self], kwargs=None)
            for target in [_killer_thread, _feeder_thread, _results_thread]
        ]
        for t in self._threads:
            t.start()
        LOGGER.debug("Threads started, spawning workers...")
        LOGGER.debug("Starting the pool with %s", {self._nb_workers})

        # Startup workers
        for _ in range(self._nb_workers):
            self._spawn_worker()
        LOGGER.info("WorkerPoolExecutor is started")

    def health_check(self):
        if self._state in FINAL_STATES:
            return
        if any([not _safe_is_alive(p) for p in self._processes.values()]):
            LOGGER.warning("At least one process died for an unknown reason, marking pool as broken")
            self._state = PoolState.BROKEN
            self.shutdown(wait=False, timeout=1)

    def _spawn_worker(self):
        # Daemon means process are linked to main one, and will be stopped if current process is stopped
        p = self._mp_context.Process(
            target=_process_worker,
            name=f"{self._prefix}_worker_process",
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
    ) -> GiskardFuture:
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if self._state in FINAL_STATES:
            raise RuntimeError(f"Cannot submit when pool is {self._state.name}")
        task = GiskardTask(callable=fn, args=args, kwargs=kwargs)
        res = GiskardFuture()
        self._futures_mapping[task.id] = res
        self._pending_tasks_queue.put(task)
        if timeout is not None:
            self._with_timeout_tasks.append(TimeoutData(task.id, time.monotonic() + timeout))
        return res

    def shutdown(self, wait=True, timeout: float = 5, force=False):
        if self._state in FINAL_STATES and not force:
            return
        # Changing state, so that thread will stop
        # Killer thread will also do cleanup
        if not force:
            self._state = PoolState.STOPPING
        # Cancelling all futures we have
        for future in self._futures_mapping.values():
            if future.cancel() and not future.done():
                future.set_exception(CancelledError("Executor is stopping"))
        # Emptying running_tasks queue
        while not self._running_tasks_queue.empty():
            try:
                self._running_tasks_queue.get_nowait()
            except ValueError as e:
                # This happens if queues is closed
                LOGGER.warning("Running task queue is already closed")
                LOGGER.exception(e)
            except Empty as e:
                # May happen if a process consume an element
                LOGGER.warning("Queue was empty, skipping")
                LOGGER.exception(e)
        # Try to nicely stop the worker, by adding None into the running tasks
        try:
            for _ in range(self._nb_workers):
                self._running_tasks_queue.put(None, timeout=1)
        except OSError as e:
            # This happens if queues is closed
            LOGGER.warning("Running task queue is already closed")
            LOGGER.exception(e)
        # Wait for process to stop by themselves
        p_list = list(self._processes.values())
        if wait:
            _wait_process_stop(p_list, timeout=timeout)
        # Clean all the queues
        for queue in [self._pending_tasks_queue, self._tasks_results, self._running_tasks_queue]:
            # In python 3.8, Simple queue seems to not have close method
            if hasattr(queue, "close"):
                queue.close()
        # Waiting for threads to finish
        for t in self._threads:
            t.join(timeout=1)
            if t.is_alive():
                LOGGER.warning("Thread %s still alive at shutdown", t.name)
        # Changing state to stopped
        self._state = PoolState.STOPPED
        # Cleaning up processes
        exit_codes = _stop_processes(p_list, timeout=1)
        self._manager.shutdown()
        return exit_codes


def _safe_get(queue: Queue, executor: WorkerPoolExecutor, timeout: float = 1) -> Tuple[Any, bool]:
    try:
        result = queue.get(timeout=1)
    except Empty:
        result = None
    except ValueError as e:
        # If queue is closed
        if executor._state not in FINAL_STATES:
            LOGGER.error("Queue is closed, and executor not in final state")
            executor._state = PoolState.BROKEN
            raise e
        return None, True
    if executor._state in FINAL_STATES:
        return None, True
    return result, False


def _results_thread(
    executor: WorkerPoolExecutor,
):
    # Goal of this thread is to feed the running tasks from pending one as soon as possible
    # while True:
    while executor._state not in FINAL_STATES:
        result, should_stop = _safe_get(executor._tasks_results, executor)
        if should_stop:
            return
        if result is None:
            continue

        future = executor._futures_mapping.pop(result.id, None)
        if future is None or future.cancelled():
            continue
        future.logs = result.logs
        if result.exception is None:
            future.set_result(result.result)
        else:
            future.set_exception(RuntimeError(result.exception))


def _feeder_thread(
    executor: WorkerPoolExecutor,
):
    # Goal of this thread is to feed the running tasks from pending one as soon as possible
    while executor._state not in FINAL_STATES:
        task, should_stop = _safe_get(executor._pending_tasks_queue, executor)
        if should_stop:
            return
        if task is None:
            continue

        future = executor._futures_mapping.get(task.id)
        if future is None:
            continue
        if future.set_running_or_notify_cancel():
            executor._running_tasks_queue.put(task)
        else:
            # Future has been cancelled already, nothing to do
            executor._futures_mapping.pop(task.id, False)


def _killer_thread(
    executor: WorkerPoolExecutor,
):
    while executor._state not in FINAL_STATES:
        while len(executor._with_timeout_tasks) == 0 and executor._state not in FINAL_STATES:
            # No need to be too active
            sleep(1)
            if executor._state not in FINAL_STATES:
                executor.health_check()
        if executor._state in FINAL_STATES:
            return

        clean_up: List[TimeoutData] = []
        exception = None
        for timeout_data in executor._with_timeout_tasks:
            if timeout_data.id not in executor._futures_mapping:
                # Task is already completed, do not wait for it
                clean_up.append(timeout_data)
            elif time.monotonic() > timeout_data.end_time:
                # Task has timed out, we should kill it
                try:
                    future = executor._futures_mapping.pop(timeout_data.id, None)
                    if future is not None and not future.cancel():
                        LOGGER.warning("Killing a timed out process")
                        future.set_exception(TimeoutError("Task took too long"))
                        pid = executor._running_process.pop(timeout_data.id, None)
                        if pid is not None:
                            p = executor._processes.pop(pid)
                            _stop_processes([p])
                            if executor._state not in FINAL_STATES:
                                executor._spawn_worker()
                except BaseException as e:
                    # This is probably an OSError, but we want to be extra safe
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
