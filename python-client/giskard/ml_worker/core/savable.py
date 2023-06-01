import logging
import os
import posixpath

from pathlib import Path
from typing import Optional, TypeVar, Generic

import cloudpickle

from giskard.client.giskard_client import GiskardClient
from giskard.core.core import SavableMeta
from giskard.settings import settings

logger = logging.getLogger(__name__)


DT = TypeVar('DT')
SMT = TypeVar('SMT', bound=SavableMeta)


class Savable(Generic[DT, SMT]):

    data: DT
    meta: SMT

    def __init__(self, data: DT, meta: SMT):
        self.data = data
        self.meta = meta

    @classmethod
    def _get_name(cls) -> str:
        return f"{cls.__class__.__name__.lower()}s"

    def _should_save_locally(self) -> bool:
        return True

    def _should_upload(self) -> bool:
        return True

    @classmethod
    def _get_meta_endpoint(cls, uuid: str, project_key: Optional[str]):
        if project_key is None:
            posixpath.join(cls._get_name(), uuid)
        else:
            posixpath.join("project", project_key, cls._get_name(), uuid)

    def _save_to_local_dir(self, local_dir: Path):
        with open(Path(local_dir) / 'data.pkl', 'wb') as f:
            cloudpickle.dump(type(self.data), f)

    def _save(self, project_key: Optional[str] = None) -> Optional[Path]:
        if not self._should_save_locally():
            return None

        name = self._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / self.meta.uuid

        if not local_dir.exists():
            os.makedirs(local_dir)
            self._save_to_local_dir(local_dir)
            logger.debug(f"Saved {name}.{self.meta.uuid}")
            return local_dir
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
    def load(cls, uuid: str, client: GiskardClient, project_key: Optional[str]):
        meta = client.load_meta(cls._get_meta_endpoint(uuid, project_key))

        name = cls._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / uuid
        # check cache first
        data = cls._read_from_local_dir(local_dir, meta)

        if data is None:
            if client is None:
                # internal worker case, no token based http client
                assert f"Cannot find existing {name} {uuid}"
            client.load_artifact(local_dir, posixpath.join(project_key or "global", name, uuid))

        return cls._read_from_local_dir(local_dir, meta)


    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: SMT):
        if not local_dir.exists():
            return None
        with open(Path(local_dir) / 'data.pkl', 'rb') as f:
            return cls(cloudpickle.load(f), meta)

