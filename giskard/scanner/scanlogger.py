from typing import Literal, Optional, Union

import enum

from giskard.core.validation import configured_validate_arguments
from giskard.utils.xprint import Template, xprint


class ScanLoggerLevel(enum.Enum):
    DEBUG = 10
    INFO = 20
    CRITICAL = 50


LoggerLevel = Union[ScanLoggerLevel, Literal["DEBUG", "INFO", "CRITICAL"]]


class ScanLogger:
    level: ScanLoggerLevel = ScanLoggerLevel.INFO

    @configured_validate_arguments
    def setLevel(self, level: LoggerLevel):
        if isinstance(level, ScanLoggerLevel):
            self.level = level
        else:
            self.level = ScanLoggerLevel[level]

    def debug(
        self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        **kwargs,
    ):
        if self.level.value <= ScanLoggerLevel.DEBUG.value:
            xprint(*args, template=template, filename=filename, **kwargs)

    def info(
        self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        **kwargs,
    ):
        if self.level.value <= ScanLoggerLevel.INFO.value:
            xprint(*args, template=template, filename=filename, **kwargs)

    def critical(
        self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        **kwargs,
    ):
        if self.level.value <= ScanLoggerLevel.CRITICAL.value:
            xprint(*args, template=template, filename=filename, **kwargs)


logger = ScanLogger()
