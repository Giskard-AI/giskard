import logging
import os
import posixpath

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TypeVar, Generic

import cloudpickle

from giskard.client.giskard_client import GiskardClient
from giskard.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class SavableMeta:
    uuid: Optional[str]


DT = TypeVar('DT')
SMT = TypeVar('SMT', bound=SavableMeta)


class Savable(Generic[DT, SMT]):

    @classmethod
    def _get_name(cls) -> str:
        return cls.__class__.__name__.lower()

    def _get_uuid(self) -> str:
        pass

    def _should_save_locally(self) -> bool:
        return True

    def _should_upload(self) -> bool:
        return True

    def _save_meta(self, client: GiskardClient, project_key: Optional[str] = None):
        pass

    def _save_to_local_dir(self, local_dir: Path):
        pass

    def _save(self, project_key: Optional[str] = None) -> Optional[Path]:
        if not self._should_save_locally():
            return None

        name = self._get_name()
        uuid = self._get_uuid()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / uuid

        if not local_dir.exists():
            os.makedirs(local_dir)
            self._save_to_local_dir(local_dir)
            logger.debug(f"Saved {name}.{uuid}")
            return local_dir

        else:
            logger.debug(f"Skipping saving of {name}.{uuid} because it is already saved")
            return local_dir

    def upload(self, client: GiskardClient, project_key: Optional[str] = None) -> str:
        name = self._get_name()

        # Do not save already saved class
        if not self._should_upload():
            logger.debug(f"Skipping upload of {name}.{self._get_uuid()} because it is already uploaded")
            return self._get_uuid()

        local_dir = self._save(project_key)

        if local_dir is not None:
            client.log_artifacts(local_dir, posixpath.join(project_key or "global", name, self._get_uuid()))

        self._save_meta(client, project_key)

        return self._get_uuid()

    @classmethod
    def load(cls, uuid: str, client: GiskardClient, project_key: Optional[str]):
        meta = cls._load_meta(uuid, client, project_key)

        name = cls._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / uuid
        # check cache first
        data = cls._read_from_local_dir(local_dir, meta)

        if data is None:
            if client is None:
                # internal worker case, no token based http client
                assert f"Cannot find existing {name} {uuid}"
            client.load_artifact(local_dir, posixpath.join(project_key or "global", name, uuid))

        data = cls._read_from_local_dir(local_dir, meta)

        return cls(data, meta, True)

    @classmethod
    def _load_meta(cls, uuid: str, client: GiskardClient, project_key: Optional[str]) -> DT:
        pass

    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: SMT) -> Optional[DT]:
        if not local_dir.exists():
            return None
        else:
            with open(Path(local_dir) / 'data.pkl', 'rb') as f:
                return cloudpickle.load(f)


@dataclass
class DatasetMeta(SavableMeta):
    pass


class Dataset(Savable[DatasetMeta]):
    pass


def test():
    Dataset().save(None)
