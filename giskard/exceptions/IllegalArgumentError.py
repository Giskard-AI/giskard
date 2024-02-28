from enum import Enum


class StatusCode(str, Enum):
    NO_ERROR = "NO_ERROR"
    INTERNAL = "INTERNAL"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"


class CodedError(Exception):
    code: StatusCode = StatusCode.INTERNAL

    def __init__(self, code: StatusCode, *args: object) -> None:
        super().__init__(*args)
        self.code = code


class IllegalArgumentError(CodedError):
    def __init__(self, *args: object) -> None:
        super().__init__(StatusCode.INVALID_ARGUMENT, *args)
