import logging
import time

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.db.session import SessionLocal
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        # Try to create session to check if DB is awake
        db = SessionLocal()
        db.execute("SELECT 1")
        time.sleep(5)  # to avoid random initialization failures
        logger.info("Creating initial data for tests")
        init_db(db)
        logger.info("Initial data created for tests")
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Initializing service for tests")
    init()
    logger.info("Service finished initializing for tests")


if __name__ == "__main__":
    main()
