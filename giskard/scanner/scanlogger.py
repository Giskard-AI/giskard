import enum
from typing import Optional

from giskard.scanner.xprint import (
    BLACK_STYLE,
    BLUE_STYLE,
    BOLD,
    CHARS_LIMIT,
    CYAN_STYLE,
    GREEN_STYLE,
    MAGENTA_STYLE,
    RED_STYLE,
    WHITE_STYLE,
    YELLOW_STYLE,
    Template,
    xprint,
)
    
class ScanLoggerLevel(enum.Enum):
    DEBUG = 0
    INFO = 5
    CRITICAL = 10

class ScanLogger:
    level: ScanLoggerLevel = ScanLoggerLevel.INFO
    
    def setLevel(self, 
        level: ScanLoggerLevel
    ):
        if not isinstance(level, ScanLoggerLevel):
            raise ValueError("Invalid log level. Please provide a ScanLoggerLevel enum.")
        self.level = level
        
    def checkLevel(self):
        return self.level.name
        
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
logger.setLevel(ScanLoggerLevel.INFO)