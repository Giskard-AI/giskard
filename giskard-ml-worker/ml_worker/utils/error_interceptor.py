import functools
import logging
import traceback
from typing import Callable, Union, Iterable

import grpc
from google.protobuf import any_pb2
from google.protobuf.message import Message
from google.rpc.error_details_pb2 import DebugInfo
from google.rpc.status_pb2 import Status
from grpc import ServicerContext, StatusCode
from grpc.experimental import wrap_server_method_handler
from grpc_status import rpc_status

from ml_worker.exceptions.IllegalArgumentError import CodedError

MESSAGE_TYPE = Union[Message, Iterable[Message]]


class ErrorInterceptor(grpc.ServerInterceptor):

    @staticmethod
    def terminate_with_exception(error_code: StatusCode, e: Exception, context: ServicerContext):
        detail = any_pb2.Any()
        detail.Pack(
            DebugInfo(
                stack_entries=traceback.format_stack(),
                detail=str(e),
            )
        )
        code, _ = error_code.value
        rich_status = Status(
            code=code,
            message=e.__class__.__name__,
            details=[detail]
        )
        context.abort_with_status(rpc_status.to_status(rich_status))

    @staticmethod
    def _wrapper(behavior: Callable[[MESSAGE_TYPE, ServicerContext], MESSAGE_TYPE]) \
            -> Callable[[MESSAGE_TYPE, ServicerContext], Message]:

        @functools.wraps(behavior)
        def wrapper(request: MESSAGE_TYPE, context: ServicerContext) -> MESSAGE_TYPE:
            try:
                return behavior(request, context)
            except CodedError as e:
                logging.exception(e)
                ErrorInterceptor.terminate_with_exception(e.code, e, context)
            except Exception as e:
                logging.exception(e)
                ErrorInterceptor.terminate_with_exception(StatusCode.INTERNAL, e, context)

        return wrapper

    def intercept_service(self, continuation, handler_call_details):
        return wrap_server_method_handler(ErrorInterceptor._wrapper, continuation(handler_call_details))
