from pathlib import Path

from giskard.settings import settings

run_dir = settings.home_dir / "run"
projects_dir = settings.home_dir / "projects"


def model_path(project_key: str, file_name: str) -> Path:
    return projects_dir / project_key / "models" / file_name


def dataset_path(project_key: str, file_name: str) -> Path:
    return projects_dir / project_key / "datasets" / file_name


def get_size(path: str):
    size = 0

    for file_ in Path(path).rglob("*"):
        size += file_.stat().st_size

    return size
