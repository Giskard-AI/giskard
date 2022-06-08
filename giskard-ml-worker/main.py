import logging
from concurrent import futures

import grpc

from generated.ml_worker_pb2_grpc import add_MLWorkerServicer_to_server
from ml_worker.server.ml_worker_service import MLWorkerServiceImpl
from ml_worker.utils.error_interceptor import ErrorInterceptor
from ml_worker.utils.logging import load_logging_config
from settings import Settings

settings = Settings()

load_logging_config()
logger = logging.getLogger()


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(
            max_workers=settings.max_workers,
            thread_name_prefix="MLWorkerExecutor",
        ),
        interceptors=[ErrorInterceptor()],
        options=[
            ('grpc.max_send_message_length', settings.max_send_message_length_mb * 1024 ** 2),
            ('grpc.max_receive_message_length', settings.max_receive_message_length_mb * 1024 ** 2),
        ]
    )

    add_MLWorkerServicer_to_server(MLWorkerServiceImpl(), server)
    server.add_insecure_port(f'{settings.host}:{settings.port}')
    server.start()
    logging.info(f"Started ML Worker server: {settings}")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
