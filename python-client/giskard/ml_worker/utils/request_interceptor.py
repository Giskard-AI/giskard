import asyncio
import functools
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Union, Awaitable

import grpc
from google.protobuf import any_pb2
from google.protobuf.message import Message
from google.rpc.status_pb2 import Status
from grpc import ServicerContext, StatusCode, aio
from grpc.experimental import wrap_server_method_handler
from grpc_status import rpc_status

from giskard.ml_worker.exceptions.IllegalArgumentError import CodedError
from giskard.ml_worker.generated.ml_worker_pb2 import MLWorkerErrorInfo

MESSAGE_TYPE = Union[Message, Iterable[Message]]

logger = logging.getLogger(__name__)

pool = ThreadPoolExecutor(thread_name_prefix="ml_worker_thread")


class MLWorkerRequestInterceptor(grpc.aio.ServerInterceptor):
    @staticmethod
    async def terminate_with_exception(error_code: StatusCode, e: Exception, context: ServicerContext):
        detail = any_pb2.Any()
        detail.Pack(
            MLWorkerErrorInfo(
                stack=traceback.format_exc(),
                error=str(e),
            )
        )
        code, _ = error_code.value
        rich_status = Status(code=code, message=e.__class__.__name__, details=[detail])
        await context.abort_with_status(rpc_status.to_status(rich_status))

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        def _wrapper(behavior):
            @functools.wraps(behavior)
            async def wrapper(request, context: aio.ServicerContext):
                try:
                    loop = asyncio.get_running_loop()
                    res = await loop.run_in_executor(pool, behavior, request, context)
                    return res
                except CodedError as e:
                    logger.exception(e)
                    await MLWorkerRequestInterceptor.terminate_with_exception(e.code, e, context)
                except Exception as e:
                    logger.exception(e)
                    await MLWorkerRequestInterceptor.terminate_with_exception(StatusCode.INTERNAL, e, context)

            return wrapper

        handler = await continuation(handler_call_details)
        if handler and (handler.request_streaming or handler.response_streaming):
            return handler

        return wrap_server_method_handler(_wrapper, handler)
