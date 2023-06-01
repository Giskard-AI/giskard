import io
import logging

logger_one = logging.getLogger('shrubbery')
logger_two = logging.getLogger(__name__)


class LogListener:
    stream: io.StringIO
    stream_handler = logging.StreamHandler

    def __init__(self):
        self.stream = io.StringIO()
        self.stream_handler = logging.StreamHandler(self.stream)
        self.stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.root.addHandler(self.stream_handler)

    def close(self) -> str:
        logging.root.removeHandler(self.stream_handler)
        logs = self.stream.getvalue()
        self.stream.close()
        return logs
