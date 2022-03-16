import logging
import threading
from pathlib import Path

import grpc

import ml_worker_pb2
from ml_worker_pb2_grpc import MLWorkerServicer
from mltask_server_runner import settings

logger = logging.getLogger()


class MLTaskServer(MLWorkerServicer):
    models_store = {}
    counter = 0

    def __init__(self, start_counter=0) -> None:
        super().__init__()
        self.counter = start_counter

    def loadModel(self, request: ml_worker_pb2.LoadModelRequest,
                  context: grpc.ServicerContext) -> ml_worker_pb2.LoadModelResponse:
        self.counter += 1
        return ml_worker_pb2.LoadModelResponse(
            message=f"RESPONSE[{threading.current_thread().name}]: {request.name} = {self.counter}")

    def predict(self, request: ml_worker_pb2.PredictRequest,
                context: grpc.ServicerContext) -> ml_worker_pb2.PredictResponse:
        logger.info(f'Running a model: {request.model_path}')
        model_path = settings.storage_root / request.model_path
        return ml_worker_pb2.PredictResponse(prediction_string="HELLO WORLD", probabilities={"asd": 123.321})
