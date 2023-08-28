from enum import Enum


class StatusCode(Enum):
    NO_ERROR = 0
    INTERNAL = 1
    INVALID_ARGUMENT = 2


class CodedError(Exception):
    code: StatusCode = StatusCode.INTERNAL

    def __init__(self, code: StatusCode, *args: object) -> None:
        super().__init__(*args)
        self.code = code


class IllegalArgumentError(CodedError):
    def __init__(self, *args: object) -> None:
        super().__init__(StatusCode.INVALID_ARGUMENT, *args)
