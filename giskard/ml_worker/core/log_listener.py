import io
import logging
import threading

logger_one = logging.getLogger("shrubbery")
logger_two = logging.getLogger(__name__)


class ThreadLogFilter(logging.Filter):
    thread_ident: int

    def __init__(self, thread_ident: int):
        super().__init__()
        self.thread_ident = thread_ident

    def filter(self, record):
        return record.thread == self.thread_ident


class LogListener:
    stream: io.StringIO
    stream_handler = logging.StreamHandler

    def __init__(self):
        self.stream = io.StringIO()
        self.stream_handler = logging.StreamHandler(self.stream)
        self.stream_handler.addFilter(ThreadLogFilter(threading.currentThread().ident))
        self.stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.root.addHandler(self.stream_handler)

    def close(self) -> str:
        logging.root.removeHandler(self.stream_handler)

        logs = self.stream.getvalue()
        self.stream.close()
        return logs
