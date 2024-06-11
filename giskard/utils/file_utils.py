from pathlib import Path
from uuid import UUID

from giskard.settings import settings


def get_file_name(name: str, extension: str, sample: bool):
    return f"{name}.sample.{extension}" if sample else f"{name}.{extension}"


def job_logs_path(job_id: UUID) -> Path:
    return settings.home_dir / "run" / "jobs" / (str(job_id) + ".log")
