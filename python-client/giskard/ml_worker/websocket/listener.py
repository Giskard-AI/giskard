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

from giskard.ml_worker import websocket
from giskard.ml_worker.websocket import (
    EchoMsg,
    ExplainParam,
    GetInfoParam,
    RunModelParam,
    TestSuiteParam,
    ExplainTextParam,
    RunAdHocTestParam,
    DatesetProcessingParam,
    GenerateTestSuiteParam,
    RunModelForDataFrameParam,
)

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
            logger.debug(f'Registered "{callback.__name__}" for ML Worker "{action.name}"')

            def wrapped_callback(ml_worker, req: dict, *args, **kwargs):
                # Parse the response ID
                rep_id = req["id"] if "id" in req.keys() else None
                # Parse the param
                params = req["param"] if "param" in req.keys() else {}
                try:
                    # TODO: Sort by usage frequency
                    if action == MLWorkerAction.getInfo:
                        params = GetInfoParam.parse_obj(params)
                    elif action == MLWorkerAction.runAdHocTest:
                        params = RunAdHocTestParam.parse_obj(params)
                    elif action == MLWorkerAction.datasetProcessing:
                        params = DatesetProcessingParam.parse_obj(params)
                    elif action == MLWorkerAction.runTestSuite:
                        params = TestSuiteParam.parse_obj(params)
                    elif action == MLWorkerAction.runModel:
                        params = RunModelParam.parse_obj(params)
                    elif action == MLWorkerAction.runModelForDataFrame:
                        params = RunModelForDataFrameParam.parse_obj(params)
                    elif action == MLWorkerAction.explain:
                        params = ExplainParam.parse_obj(params)
                    elif action == MLWorkerAction.explainText:
                        params = ExplainTextParam.parse_obj(params)
                    elif action == MLWorkerAction.echo:
                        params = EchoMsg.parse_obj(params)
                    elif action == MLWorkerAction.generateTestSuite:
                        params = GenerateTestSuiteParam.parse_obj(params)
                    elif action == MLWorkerAction.stopWorker:
                        pass
                    elif action == MLWorkerAction.getCatalog:
                        pass
                    elif action == MLWorkerAction.generateQueryBasedSlicingFunction:
                        pass
                    # Call the function and get the response
                    info: websocket.WorkerReply = callback(
                        ml_worker=ml_worker, action=action.name, params=params, *args, **kwargs
                    )
                except Exception as e:
                    info: websocket.WorkerReply = websocket.ErrorReply(error_str=str(e), error_type=type(e).__name__)

                if rep_id:
                    # Reply if there is an ID
                    logger.debug(f"[WRAPPED_CALLBACK] replying {info.json()} for {action.name}")
                    ml_worker.ws_conn.send(
                        f"/app/ml-worker/{ml_worker.ml_worker_id}/rep",
                        json.dumps({"id": rep_id, "action": action.name, "payload": info.json() if info else "{}"}),
                    )

            WEBSOCKET_ACTORS[action.name] = wrapped_callback
        return callback

    return websocket_actor_callback


class MLWorkerWebSocketListener(stomp.ConnectionListener):
    def __init__(self, worker):
        self.ml_worker = worker

    def on_error(self, frame):
        logger.debug(f"received an error {frame.body}")

    def on_disconnected(self):
        logger.debug("disconnected")
        # Attemp to reconnect
        self.ml_worker.connect_websocket_client()

    def on_message(self, frame):
        logger.debug(f"received a message {frame.cmd} {frame.headers} {frame.body}")
        req = json.loads(frame.body)
        if "action" in req.keys() and req["action"] in WEBSOCKET_ACTORS:
            # Dispatch the action
            WEBSOCKET_ACTORS[req["action"]](self.ml_worker, req)


@websocket_actor(MLWorkerAction.getInfo)
def on_ml_worker_get_info(ml_worker, params: GetInfoParam, *args, **kwargs) -> dict:
    logger.info("Collecting ML Worker info from WebSocket")

    installed_packages = (
        {p.project_name: p.version for p in pkg_resources.working_set} if params.list_packages else None
    )
    current_process = psutil.Process(os.getpid())
    return websocket.GetInfo(
        platform=websocket.Platform(
            machine=platform.uname().machine,
            node=platform.uname().node,
            processor=platform.uname().processor,
            release=platform.uname().release,
            system=platform.uname().system,
            version=platform.uname().version,
        ),
        giskardClientVersion=giskard.__version__,
        pid=os.getpid(),
        processStartTime=int(current_process.create_time()),
        interpreter=sys.executable,
        interpreterVersion=platform.python_version(),
        installedPackages=installed_packages,
        internalGrpcAddress=ml_worker.ml_worker_id,
        isRemote=ml_worker.tunnel is not None,
    )


@websocket_actor(MLWorkerAction.stopWorker)
def on_ml_worker_stop_worker(ml_worker, *args, **kwargs):
    # FIXME: Stop the server properly
    asyncio.get_event_loop().create_task(ml_worker.stop())
    return websocket.Empty()
