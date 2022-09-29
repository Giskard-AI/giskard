from grpc import StatusCode


class CodedError(Exception):
    code: StatusCode = StatusCode.INTERNAL

    def __init__(self, code: StatusCode, *args: object) -> None:
        super().__init__(*args)
        self.code = code


class IllegalArgumentError(CodedError):
    def __init__(self, *args: object) -> None:
        super().__init__(StatusCode.INVALID_ARGUMENT, *args)
