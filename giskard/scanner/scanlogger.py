import enum
from typing import Optional

from giskard.utils.xprint import (
    Template,
    xprint,
)

class ScanLoggerLevel(enum.Enum):
    DEBUG = 0
    INFO = 5
    CRITICAL = 10

class ScanLogger:
    level: ScanLoggerLevel = ScanLoggerLevel.INFO
    
    def setLevel(self, level: str):
        level_map = {
            "DEBUG": ScanLoggerLevel.DEBUG,
            "INFO": ScanLoggerLevel.INFO,
            "CRITICAL": ScanLoggerLevel.CRITICAL
        }

        if level not in level_map:
            raise ValueError(f"Invalid log level: {level}. Please provide 'DEBUG', 'INFO', or 'CRITICAL'.")
        
        self.level = level_map[level]
        
    def debug(self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        **kwargs,
    ):
        if self.level.value <= ScanLoggerLevel.DEBUG.value :
            xprint(*args, template = template, filename = filename, **kwargs)
    
    def info(self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        **kwargs,
    ):
        if self.level.value <= ScanLoggerLevel.INFO.value :
            xprint(*args, template = template, filename = filename, **kwargs)
    
    def critical(self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        **kwargs,
    ):
        if self.level.value <= ScanLoggerLevel.CRITICAL.value :
            xprint(*args, template = template, filename = filename, **kwargs)
    
logger = ScanLogger()