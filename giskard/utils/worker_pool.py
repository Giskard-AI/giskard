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
from multiprocessing import Process, Queue, cpu_count, get_context
from multiprocessing.context import SpawnContext, SpawnProcess
from multiprocessing.managers import SyncManager
from queue import Empty, Full
from threading import Thread, current_thread
from time import sleep
from uuid import uuid4

from giskard.ml_worker.utils.cache import CACHE

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
class GiskardMLWorkerExceptionInfo:
    type: str
    message: str
    stack_trace: str


@dataclass(frozen=True)
class GiskardResult:
    id: str
    logs: str
    result: Any = None
    exception: Optional[GiskardMLWorkerExceptionInfo] = None


def _process_worker(tasks_queue: Queue, tasks_results: Queue, running_process: Dict[str, str], cache_content):
    pid = os.getpid()
    LOGGER.info("Process %s started", pid)
    CACHE.start(*cache_content)
    LOGGER.info("Shared cache initializd")

    while True:
        # Blocking accessor, will wait for a task
        try:
            task: Optional[GiskardTask] = tasks_queue.get(timeout=1)
        except Empty:
            continue
        # This is how we cleanly stop the workers
        if task is None:
            LOGGER.info("Process %s stopping", pid)
            return
        # Capture any log (stdout, stderr + root logger)
        with redirect_stdout(StringIO()) as f:
            with redirect_stderr(f):
                handler = logging.StreamHandler(f)
                logging.getLogger().addHandler(handler)
                to_return = None
                try:
                    LOGGER.debug("Doing task %s", task.id)
                    running_process[task.id] = pid
                    result = task.callable(*task.args, **task.kwargs)
                    to_return = GiskardResult(id=task.id, result=result, logs=f.getvalue())
                except BaseException as e:
                    exception = GiskardMLWorkerExceptionInfo(
                        type=type(e).__name__,
                        message=str(e),
                        stack_trace=traceback.format_exc(),
                    )
                    to_return = GiskardResult(
                        id=task.id, exception=exception, logs=f.getvalue() + "\n" + str(exception.stack_trace)
                    )
                finally:
                    running_process.pop(task.id)
                    tasks_results.put(to_return)
                    logging.getLogger().removeHandler(handler)


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
        self.processes: Dict[int, SpawnProcess] = {}
        # Manager to handle shared object
        self._manager: SyncManager = self._mp_context.Manager()
        cache_content = self._manager.dict()
        cache_keys = self._manager.list()
        CACHE.start(cache_content, cache_keys)
        # Mapping of the running tasks and worker pids
        self.running_process: Dict[str, str] = self._manager.dict()
        # Mapping of the running tasks and worker pids
        self.with_timeout_tasks: List[TimeoutData] = []
        # Queue with tasks to run
        self.pending_tasks_queue: Queue = self._mp_context.Queue()
        # Queue with tasks to be consumed asap
        # As in ProcessPool, add one more to avoid idling process
        self.running_tasks_queue: Queue = self._mp_context.Queue(maxsize=self._nb_workers + 1)
        # Queue with results to notify
        self.tasks_results: Queue = self._mp_context.Queue()
        # Mapping task_id with future
        self.futures_mapping: Dict[str, Future] = dict()
        LOGGER.debug("Starting threads for the WorkerPoolExecutor")

        self._threads = [
            Thread(
                name=f"{self._prefix}{target.__name__}",
                target=target,
                daemon=True,
                args=[self],
                kwargs=None,
            )
            for target in [_killer_thread, _feeder_thread, _results_thread]
        ]
        for t in self._threads:
            t.start()
        LOGGER.debug("Threads started, spawning workers...")
        LOGGER.debug("Starting the pool with %s", {self._nb_workers})

        # Startup workers
        for _ in range(self._nb_workers):
            self.spawn_worker()
        LOGGER.info("WorkerPoolExecutor is started")

    def terminated(self) -> bool:
        return self._state in FINAL_STATES

    def safe_get(self, queue: Queue, timeout: float = 1) -> Tuple[Any, bool]:
        try:
            result = queue.get(timeout=timeout)
        except Empty:
            result = None
        except (ValueError, OSError) as e:
            # If queue is closed
            if not self.terminated():
                LOGGER.error("Queue is closed, and executor not in final state")
                LOGGER.exception(e)
                self._state = PoolState.BROKEN
                raise e
            return None, True
        if self.terminated():
            return None, True
        return result, False

    def health_check(self):
        if self.terminated():
            return
        broken_pool = False
        if any([not t.is_alive() for t in self._threads]):
            LOGGER.error("At least one thread died for an unknown reason, marking pool as broken")
            LOGGER.error("Dead threads: %s", [t.name for t in self._threads if not t.is_alive()])
            broken_pool = True
        if any([not _safe_is_alive(p) for p in self.processes.values()]):
            LOGGER.error("At least one process died for an unknown reason, marking pool as broken")
            LOGGER.error(
                "Non null exit codes: %s",
                [_safe_exit_code(p) for p in self.processes.values() if _safe_exit_code(p) != 0],
            )
            broken_pool = True
        if broken_pool:
            self._state = PoolState.BROKEN
            self.shutdown(wait=True, force=True, cancel_futures=True, timeout=30)
            raise RuntimeError("Pool is broken, read previous logs")

    def spawn_worker(self):
        # Daemon means process are linked to main one, and will be stopped if current process is stopped
        p = self._mp_context.Process(
            target=_process_worker,
            name=f"{self._prefix}_worker_process",
            args=(self.running_tasks_queue, self.tasks_results, self.running_process, CACHE.content()),
            daemon=True,
        )
        p.start()
        self.processes[p.pid] = p
        LOGGER.info("Starting a new worker %s", p.pid)

    def kill_task(self, task_id: str) -> Optional[BaseException]:
        # Task has timed out, we should kill it
        try:
            future = self.futures_mapping.pop(task_id, None)
            if future is not None and not future.cancel():
                LOGGER.warning("Killing a timed out process")
                future.set_exception(TimeoutError("Task took too long"))
                pid = self.running_process.pop(task_id, None)
                if pid is not None:
                    p = self.processes.pop(pid)
                    _stop_processes([p])
                    if not self.terminated():
                        self.spawn_worker()
        except BaseException as e:
            # This is probably an OSError, but we want to be extra safe
            LOGGER.warning("Unexpected error when killing a timed out process, pool is broken")
            LOGGER.exception(e)
            self._state = PoolState.BROKEN
            return e

    def submit(self, fn, /, *args, **kwargs):
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
        if self.terminated():
            raise RuntimeError(f"Cannot submit when pool is {self._state.name}")
        task = GiskardTask(callable=fn, args=args, kwargs=kwargs)
        res = GiskardFuture()
        self.futures_mapping[task.id] = res
        self.pending_tasks_queue.put(task)
        if timeout is not None:
            self.with_timeout_tasks.append(TimeoutData(task.id, time.monotonic() + timeout))
        return res

    def shutdown(self, wait=True, *, cancel_futures=True, timeout: float = 30, force=False):
        if self.terminated() and not force:
            return
        # Changing state, so that thread will stop
        if not force:
            self._state = PoolState.STOPPING
        # Cancelling all futures we have
        if cancel_futures:
            for future in self.futures_mapping.values():
                if not future.cancel() and not future.done():
                    future.set_exception(CancelledError("Executor is stopping"))
        # Emptying running_tasks queue
        try:
            while not self.running_tasks_queue.empty():
                task: GiskardTask = self.running_tasks_queue.get(timeout=0.5)
                self.kill_task(task.id)
        except (ValueError, Empty, OSError) as e:
            LOGGER.warning("Error while emptying running queue")
            LOGGER.exception(e)
        # Try to nicely stop the worker, by adding None into the running tasks
        try:
            for _ in range(self._nb_workers):
                self.running_tasks_queue.put(None, timeout=1)
        except (ValueError, Full, OSError) as e:
            LOGGER.warning("Error while trying to feed None task to running queue")
            LOGGER.exception(e)
        # Wait for process to stop by themselves
        p_list = list(self.processes.values())
        if wait:
            _wait_process_stop(p_list, timeout=timeout)
        # Clean all the queues
        for queue in [self.pending_tasks_queue, self.tasks_results, self.running_tasks_queue]:
            # In python 3.8, Simple queue seems to not have close method
            if hasattr(queue, "close"):
                queue.close()
        # Waiting for threads to finish
        for t in self._threads:
            if t is current_thread():
                # To avoid killer thread to join itself
                continue
            t.join(timeout=timeout)
            if t.is_alive():
                LOGGER.warning("Thread %s still alive at shutdown", t.name)
                raise RuntimeError("Thread{t.name} still alive at shutdown")
        # Changing state to stopped
        if not force:
            self._state = PoolState.STOPPED
        # Cleaning up processes
        exit_codes = _stop_processes(p_list, timeout=timeout)
        self._manager.shutdown()
        return exit_codes


class GiskardMLWorkerException(Exception):
    def __init__(self, info: GiskardMLWorkerExceptionInfo):
        super().__init__(info.message)
        self.info = info


def _results_thread(
    executor: WorkerPoolExecutor,
):
    # Goal of this thread is to feed the running tasks from pending one as soon as possible
    # while True:
    while not executor.terminated():
        result, _ = executor.safe_get(executor.tasks_results)
        if result is None:
            continue

        future = executor.futures_mapping.pop(result.id, None)
        if future is None or future.done():
            continue
        future.logs = result.logs
        if result.exception is None:
            future.set_result(result.result)
        else:
            future.set_exception(GiskardMLWorkerException(result.exception))


def _feeder_thread(
    executor: WorkerPoolExecutor,
):
    # Goal of this thread is to feed the running tasks from pending one as soon as possible
    while not executor.terminated():
        task, _ = executor.safe_get(executor.pending_tasks_queue)
        if task is None:
            continue

        future = executor.futures_mapping.get(task.id)
        if future is None:
            continue
        if executor.terminated():
            future.set_exception(RuntimeError("Executor is stopping"))
            continue
        if future.set_running_or_notify_cancel():
            executor.running_tasks_queue.put(task)
        else:
            # Future has been cancelled already, nothing to do
            executor.futures_mapping.pop(task.id, False)


def _killer_thread(
    executor: WorkerPoolExecutor,
):
    while not executor.terminated():
        while len(executor.with_timeout_tasks) == 0 and not executor.terminated():
            # No need to be too active
            sleep(1)
            executor.health_check()
        if executor.terminated():
            return

        clean_up: List[TimeoutData] = []
        exception = None
        for timeout_data in executor.with_timeout_tasks:
            if timeout_data.id not in executor.futures_mapping:
                # Task is already completed, do not wait for it
                clean_up.append(timeout_data)
            elif time.monotonic() > timeout_data.end_time:
                exception = executor.kill_task(timeout_data.id)
                clean_up.append(timeout_data)
        for elt in clean_up:
            executor.with_timeout_tasks.remove(elt)

        if exception is not None:
            raise exception
