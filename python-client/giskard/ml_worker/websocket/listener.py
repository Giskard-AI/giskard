import logging

import json
import stomp


import platform
import pkg_resources
import psutil
import sys
import os
import giskard


logger = logging.getLogger(__name__)


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
        if "action" in req.keys():
            params = req["param"] if "param" in req.keys() else {}
            if req["action"] == "getInfo":
                logger.info("Collecting ML Worker info from WebSocket")
                installed_packages = (
                    {p.project_name: p.version for p in pkg_resources.working_set}
                    if "list_packages" in params.keys() and params["list_packages"]
                    else None
                )
                current_process = psutil.Process(os.getpid())
                info = {
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
                    "internalGrpcAddress": "123",  # self.ml_worker.address,
                    "isRemote": self.ml_worker.tunnel is not None,
                }
                logger.debug("Test ML Worker Collecting replying")
                if "id" in req.keys():
                    req_id = req["id"]
                    self.ml_worker.ws_conn.send(
                        f"/app/ml-worker/{self.ml_worker.ml_worker_id}/rep",
                        json.dumps({"id": req_id, "action": "getInfo", "payload": json.dumps(info)}),
                    )
