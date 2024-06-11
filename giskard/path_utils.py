from pathlib import Path

from giskard.settings import settings

run_dir = settings.home_dir / "run"
artifacts_dir = settings.home_dir / "artifacts"


def get_size(path: str):
    size = 0

    for file_ in Path(path).rglob("*"):
        size += file_.stat().st_size

    return size
