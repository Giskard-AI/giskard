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
    obj: DT
    meta: SMT
    uploaded: bool = False

    def _get_name(self) -> str:
        return self.__class__.__name__.lower()

    def _should_save_locally(self) -> bool:
        return True

    def _save_meta(self, client: GiskardClient, project_key: Optional[str] = None):
        pass

    def _save_to_local_dir(self, local_dir: Path):
        with open(Path(local_dir) / 'data.pkl', 'wb') as f:
            cloudpickle.dump(self.obj, f)

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
        if self.uploaded:
            logger.debug(f"Skipping upload of {name}.{self.meta.uuid} because it is already uploaded")
            return self.meta.uuid

        artifact_endpoint = posixpath.join(project_key or "global", name, self.meta.uuid)

        local_dir = self._save(project_key)

        if local_dir is not None:
            client.log_artifacts(local_dir, artifact_endpoint)

        self.meta = client.save_meta(self.meta, meta_endpoint)

        return self.meta.uuid


@dataclass
class DatasetMeta(SavableMeta):
    pass


class Dataset(Savable[DatasetMeta]):
    pass


def test():
    Dataset().save(None)
