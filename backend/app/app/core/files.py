from io import BytesIO
from pathlib import Path
import re
import cloudpickle

from fastapi.datastructures import UploadFile
from sqlalchemy.orm import Session
from zstandard import ZstdCompressor, ZstdDecompressor
import pandas as pd

from app.core.config import settings
from app import schemas, crud, models


def compress_for_storage(file: UploadFile) -> UploadFile:
    compressor = ZstdCompressor(level=3, write_checksum=True)
    content = compressor.compress(file.file.read())
    return UploadFile(file.filename + ".zst", BytesIO(content))


def save_dataset_file(db: Session, file: UploadFile, project: models.Project, user_id: int):
    try:
        project_files_dir = settings.BUCKET_PATH / project.key
        project_files_dir.mkdir(parents=True, exist_ok=True)
        file_path = project_files_dir / file.filename
        file_path = make_unique_path(path=file_path, num_file_extensions=2)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        # store info in DB
        data = schemas.ProjectFileCreateSchema(
            file_name=file_path.stem,
            location=str(file_path),
        )
        dataset_out = crud.dataset.create(db, data, project.id, user_id)
        return dataset_out
    except (IOError, ValueError) as e:
        raise e


def read_dataset_file(file_path: str) -> pd.DataFrame:
    try:
        df = pd.DataFrame()
        dzst = ZstdDecompressor()
        with open(file_path, "rb") as f:
            bytes_io = BytesIO(dzst.decompress(f.read()))
        if ".csv" in file_path:
            df = pd.read_csv(bytes_io)
        elif ".xls" in file_path:
            df = pd.read_excel(bytes_io)
        return df
    except Exception as e:
        raise e


def read_model_file(file_path: str) -> object:
    dzst = ZstdDecompressor()
    with open(file_path, "rb") as f:
        return cloudpickle.loads(dzst.decompress(f.read()))


def has_read_access(user: models.User, project: models.Project, file: models.ProjectFile) -> bool:
    return (
        crud.user.is_superuser(user)
        or file.owner_id == user.id
        or user.user_id in [u.user_id for u in project.guest_list]
    )


def make_unique_path(path: Path, num_file_extensions: int = 1) -> Path:
    """Creates a new unique path if it already exists

    It works by appending "_1" to the path name before the file extensions.
    If there is already a _{num} at the end of the path name, it increments by 1.

    Args:
        path: target path
        num_file_extensions: Number of file extensions
            Ex: ".csv" is 1, ".csv.zst" is 2

    Returns:
        Unique path

    """
    file_extensions = path.suffixes
    if len(file_extensions) != num_file_extensions:
        raise ValueError(
            f"Invalid number of file extensions: expected {num_file_extensions} "
            + f"but got {len(file_extensions)} in {path.name}"
        )
    if not (path.exists()):
        return path
    for _ in range(num_file_extensions - 1):  # removes file extensions from the path
        path = path.with_suffix("")
    path_stem_without_extensions = path.stem
    path_increment: str = re.findall(r"_[0-9]+$", path_stem_without_extensions)
    if path_increment:
        new_path_increment = int(path_increment[-1].replace("_", "")) + 1
        new_path_name = re.sub(
            r"_[0-9]+$", f"_{new_path_increment}", path_stem_without_extensions
        ) + "".join(file_extensions)
        new_path = path.parent / new_path_name
    else:
        new_path = path.parent / (path_stem_without_extensions + "_1" + "".join(file_extensions))
    return make_unique_path(new_path, num_file_extensions)
