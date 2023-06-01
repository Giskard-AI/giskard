import logging
import os
import posixpath
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Generic

from giskard.client.giskard_client import GiskardClient
from giskard.core.core import SMT, SavableMeta
from giskard.settings import settings

logger = logging.getLogger(__name__)


class Artifact(Generic[SMT], ABC):
    meta: SMT

    def __init__(self, meta: SMT):
        self.meta = meta

    @abstractmethod
    def save(self, local_dit: Path):
        ...

    @classmethod
    @abstractmethod
    def load(cls, local_dir: Path, uuid: str, meta: Optional[SMT]) -> 'Artifact':
        ...

    @classmethod
    def _get_meta_class(cls) -> type(SMT):
        return SavableMeta

    @classmethod
    def _get_name(cls) -> str:
        return f"{cls.__class__.__name__.lower()}s"

    @classmethod
    def _get_meta_endpoint(cls, uuid: str, project_key: Optional[str]) -> str:
        if project_key is None:
            return posixpath.join(cls._get_name(), uuid)
        else:
            return posixpath.join("project", project_key, cls._get_name(), uuid)

    def upload(self, client: GiskardClient, project_key: Optional[str] = None) -> str:
        name = self._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / self.meta.uuid

        os.makedirs(local_dir)
        self.save(local_dir)
        logger.debug(f"Saved {name}.{self.meta.uuid}")

        client.log_artifacts(local_dir, posixpath.join(project_key or "global", self._get_name(), self.meta.uuid))
        self.meta = client.save_meta(self._get_meta_endpoint(self.meta.uuid, project_key), self.meta)

        return self.meta.uuid

    @classmethod
    def download(cls, uuid: str, client: Optional[GiskardClient], project_key: Optional[str]) -> 'Artifact':
        if client is None:
            meta = None
        else:
            meta = client.load_meta(cls._get_meta_endpoint(uuid, project_key), cls._get_meta_class())

        name = cls._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / uuid

        # check cache first
        data = cls.load(local_dir, uuid, meta)

        if data is None:
            assert client is not None, f"Cannot find existing {name} {uuid}"
            client.load_artifact(local_dir, posixpath.join(project_key or "global", name, uuid))
            return cls.load(local_dir, uuid, meta)
