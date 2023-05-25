import importlib
import logging
import os
import pickle
import platform
import posixpath
import uuid
from abc import ABC
from pathlib import Path
from typing import Optional, Generic, Union

import cloudpickle
import yaml

from giskard.client.giskard_client import GiskardClient
from giskard.core.core import DT, SMT, SavableMeta, DatasetProcessFunctionType
from giskard.settings import settings

logger = logging.getLogger(__name__)

# TODO: abstract
SAVABLE_CLASS_PKL = "SavableClass.pkl"
META_FILENAME = "giskard-model-meta.yaml"


class Savable(ABC):
    should_save_class = False
    id: uuid.UUID = None

    @classmethod
    def determine_class(cls, meta, local_dir):
        class_file = Path(local_dir) / SAVABLE_CLASS_PKL
        if class_file.exists():
            with open(class_file, "rb") as f:
                clazz = cloudpickle.load(f)
                if not issubclass(clazz, Savable):
                    raise ValueError(f"Unknown class: {clazz}. Savable should inherit from 'Savable' class")
                return clazz
        else:
            return getattr(importlib.import_module(meta.loader_module), meta.loader_class)

    # TODO: abstract
    def save_meta(self, local_path):
        with open(Path(local_path) / META_FILENAME, "w") as f:
            yaml.dump({
                "language_version": platform.python_version(),
                "language": "PYTHON"
            },
                f,
                default_flow_style=False,
            )

    def save(self, local_path: Union[str, Path]) -> None:
        if self.id is None:
            self.id = uuid.uuid4()
        if self.should_save_class:
            self.save_class(local_path)
        self.save_meta(local_path)

    def save_class(self, local_path):
        class_file = Path(local_path) / SAVABLE_CLASS_PKL
        with open(class_file, "wb") as f:
            cloudpickle.dump(self.__class__, f, protocol=pickle.DEFAULT_PROTOCOL)


class Picklable(Generic[DT, SMT]):
    data: DT
    meta: SMT

    def __init__(self, data: DT, meta: SMT):
        self.data = data
        self.meta = meta

    @classmethod
    def _get_name(cls) -> str:
        return f"{cls.__class__.__name__.lower()}s"

    @classmethod
    def _get_meta_class(cls) -> type(SMT):
        return SavableMeta

    def _should_save_locally(self) -> bool:
        return True

    def _should_upload(self) -> bool:
        return True

    @classmethod
    def _get_meta_endpoint(cls, uuid: str, project_key: Optional[str]) -> str:
        if project_key is None:
            return posixpath.join(cls._get_name(), uuid)
        else:
            return posixpath.join("project", project_key, cls._get_name(), uuid)

    def _save_to_local_dir(self, local_dir: Path):
        with open(Path(local_dir) / 'data.pkl', 'wb') as f:
            cloudpickle.dump(self.data, f, protocol=pickle.DEFAULT_PROTOCOL)

    def _save(self, project_key: Optional[str] = None) -> Optional[Path]:
        if not self._should_save_locally():
            return None

        name = self._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / self.meta.uuid

        if not local_dir.exists():
            os.makedirs(local_dir)
            self._save_to_local_dir(local_dir)
            logger.debug(f"Saved {name}.{self.meta.uuid}")
        else:
            logger.debug(f"Skipping saving of {name}.{self.meta.uuid} because it is already saved")
        return local_dir

    def upload(self, client: GiskardClient, project_key: Optional[str] = None) -> str:
        name = self._get_name()
        # Do not save already saved class
        if not self._should_upload():
            return self.meta.uuid

        local_dir = self._save(project_key)

        if local_dir is not None:
            client.log_artifacts(local_dir, posixpath.join(project_key or "global", name, self.meta.uuid))

            self.meta = client.save_meta(self._get_meta_endpoint(self.meta.uuid, project_key), self.meta)

        return self.meta.uuid

    @classmethod
    def _read_meta_from_loca_dir(cls, uuid: str, project_key: Optional[str]) -> SMT:
        return SavableMeta(uuid=uuid)

    @classmethod
    def load(cls, uuid: str, client: Optional[GiskardClient], project_key: Optional[str]):
        if client is None:
            meta = cls._read_meta_from_loca_dir(uuid, project_key)
        else:
            meta = client.load_meta(cls._get_meta_endpoint(uuid, project_key), cls._get_meta_class())

        if hasattr(meta, 'process_type') and meta.process_type == DatasetProcessFunctionType.CLAUSES.name:
            return cls._load_no_code(meta)

        name = cls._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / uuid
        # check cache first
        data = cls._read_from_local_dir(local_dir, meta)

        if data is None:
            assert client is not None, f"Cannot find existing {name} {uuid}"
            client.load_artifact(local_dir, posixpath.join(project_key or "global", name, uuid))
            return cls._read_from_local_dir(local_dir, meta)
        else:
            return data

    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: SMT):
        if not local_dir.exists():
            return None
        with open(Path(local_dir) / 'data.pkl', 'rb') as f:
            return cls(cloudpickle.load(f), meta)

    @classmethod
    def _load_no_code(cls, meta: SMT):
        raise RuntimeError(f"No code function are not supported for {cls.__class__}")
