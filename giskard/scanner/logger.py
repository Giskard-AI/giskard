import logging
from .xprint import xprint, Template
from typing import Optional


class LogWrapper(logging.Logger):
    def debug(
        self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        verbose: bool = True,
        **kwargs,
    ):
        if self.isEnabledFor(logging.DEBUG):
            xprint(*args, template=template, filename=filename, verbose=verbose, **kwargs)

    def info(
        self,
        *args,
        template: Optional[Template] = None,
        filename: Optional[str] = None,
        verbose: bool = True,
        **kwargs,
    ):
        if self.isEnabledFor(logging.INFO):
            xprint(*args, template=template, filename=filename, verbose=verbose, **kwargs)


logger = LogWrapper(__name__)
logger.setLevel(logging.INFO)
