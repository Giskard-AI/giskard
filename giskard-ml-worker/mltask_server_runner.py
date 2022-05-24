import logging
import os.path
from concurrent import futures
from logging.config import fileConfig
from pathlib import Path

import grpc
from pydantic import BaseSettings
from pydantic.class_validators import validator

from generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server


class Settings(BaseSettings):
    port: int = 50051
    host: str = '0.0.0.0'
    max_workers: int = 10

    environment: str = ""

    class Config:
        env_prefix = "GSK_"


settings = Settings()


def load_logging_config():
    if settings.environment:
        config_path = f'logging_config{"." + settings.environment}.ini'
        if os.path.exists(config_path):
            fileConfig(config_path)
        else:
            print(f"Failed to load logging config from {config_path}")
    else:
        fileConfig('logging_config.ini')


load_logging_config()
logger = logging.getLogger()


def serve():
    from ml_worker.server.ml_task_server import MLTaskServer

    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=settings.max_workers,
        thread_name_prefix="MLTaskServerExecutor"
    ))
    add_MLWorkerServicer_to_server(MLTaskServer(1000), server)
    server.add_insecure_port(f'{settings.host}:{settings.port}')
    server.start()
    logging.info(f"Started ML Worker server: {settings}")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
