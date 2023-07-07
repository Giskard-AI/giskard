from enum import Enum
import logging

import json
import stomp


import platform
import pkg_resources
import psutil
import sys
import os
import giskard

import asyncio


logger = logging.getLogger(__name__)


class MLWorkerAction(Enum):
    getInfo = 0
    runAdHocTest = 1
    datasetProcessing = 2
    runTestSuite = 3
    runModel = 4
    runModelForDataFrame = 5
    explain = 6
    explainText = 7
    echo = 8
    generateTestSuite = 9
    stopWorker = 10
    getCatalog = 11
    generateQueryBasedSlicingFunction = 12


def websocket_log_actor(ml_worker, req: dict, *args, **kwargs):
    param = req["param"] if "param" in req.keys() else {}
    action = req["action"] if "action" in req.keys() else ""
    logger.info(f"ML Worker {ml_worker.ml_worker_id} performing {action} params: {param}")


WEBSOCKET_ACTORS = dict((action.name, websocket_log_actor) for action in MLWorkerAction)


def websocket_actor(action: MLWorkerAction):
    """
    Register a function as an actor to an action from WebSocket connection
    """

    def websocket_actor_callback(callback: callable):
        if action in MLWorkerAction:
            logger.info(f'Registered "{callback.__name__}" for ML Worker "{action.name}"')

            def wrapped_callback(ml_worker, req: dict, *args, **kwargs):
                # Parse the response ID
                rep_id = req["id"] if "id" in req.keys() else None
                # Parse the param
                params = req["param"] if "param" in req.keys() else {}
                # Call the function and get the response
                info = callback(ml_worker=ml_worker, action=action.name, params=params, *args, **kwargs)

                if rep_id:
                    # Reply if there is an ID
                    logger.info(f"[WRAPPED_CALLBACK] replying {info} for {action.name}")
                    ml_worker.ws_conn.send(
                        f"/app/ml-worker/{ml_worker.ml_worker_id}/rep",
                        json.dumps({"id": rep_id, "action": action.name, "payload": json.dumps(info)}),
                    )

            WEBSOCKET_ACTORS[action.name] = wrapped_callback

    return websocket_actor_callback


class MLWorkerWebSocketListener(stomp.ConnectionListener):
    def __init__(self, worker):
        self.ml_worker = worker

    def on_error(self, frame):
        logger.info(f"received an error {frame.body}")

    def on_disconnected(self):
        logger.info("disconnected")

    def on_message(self, frame):
        logger.info(f"received a message {frame.cmd} {frame.headers} {frame.body}")
        req = json.loads(frame.body)
        if "action" in req.keys() and req["action"] in WEBSOCKET_ACTORS:
            # Dispatch the action
            WEBSOCKET_ACTORS[req["action"]](self.ml_worker, req)


@websocket_actor(MLWorkerAction.getInfo)
def on_ml_worker_get_info(ml_worker, params: dict, *args, **kwargs) -> dict:
    logger.info("Collecting ML Worker info from WebSocket")

    installed_packages = (
        {p.project_name: p.version for p in pkg_resources.working_set}
        if "list_packages" in params.keys() and params["list_packages"]
        else None
    )
    current_process = psutil.Process(os.getpid())
    return {
        "platform": {
            "machine": platform.uname().machine,
            "node": platform.uname().node,
            "processor": platform.uname().processor,
            "release": platform.uname().release,
            "system": platform.uname().system,
            "version": platform.uname().version,
        },
        "giskardClientVersion": giskard.__version__,
        "pid": os.getpid(),
        "processStartTime": int(current_process.create_time()),
        "interpreter": sys.executable,
        "interpreterVersion": platform.python_version(),
        "installedPackages": installed_packages,
        "internalGrpcAddress": ml_worker.ml_worker_id,
        "isRemote": ml_worker.tunnel is not None,
    }


@websocket_actor(MLWorkerAction.stopWorker)
def on_ml_worker_stop_worker(ml_worker, *args, **kwargs):
    # FIXME: Stop the server properly
    asyncio.get_event_loop().create_task(ml_worker.stop())
    return None
