from typing import Generic, Optional, Set

import inspect
import logging
import os
import pickle
import posixpath
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import cloudpickle
import yaml

from giskard.client.giskard_client import GiskardClient
from giskard.core.core import SMT, SavableMeta
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.settings import settings

logger = logging.getLogger(__name__)


class Artifact(Generic[SMT], ABC):
    meta: SMT

    def __init__(self, meta: SMT):
        self.meta = meta

    def save(self, local_dir: Path):
        self._save_locally(local_dir)
        self._save_meta_locally(local_dir)

    @property
    def dependencies(self) -> Set["Artifact"]:
        return set()

    @abstractmethod
    def _save_locally(self, local_dit: Path):
        ...

    @classmethod
    @abstractmethod
    def load(cls, local_dir: Path, uuid: str, meta: SMT) -> "Artifact":
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

    def _save_meta_locally(self, local_dir):
        with open(Path(local_dir) / "meta.yaml", "w") as f:
            yaml.dump(self.meta, f)

    @classmethod
    def _load_meta_locally(cls, local_dir, uuid: str) -> Optional[SMT]:
        file = Path(local_dir) / "meta.yaml"
        if not file.exists():
            return None

        with open(file, "r") as f:
            # PyYAML prohibits the arbitary execution so our class cannot be loaded safely,
            # see: https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
            return yaml.load(f, Loader=yaml.UnsafeLoader)

    def upload(
        self,
        client: GiskardClient,
        project_key: Optional[str] = None,
        uploaded_dependencies: Optional[Set["Artifact"]] = None,
    ) -> str:
        """
        Uploads the slicing function and its metadata to the Giskard hub.

        Args:
            client (GiskardClient): The Giskard client instance used for communication with the hub.
            project_key (str, optional): The project key where the slicing function will be uploaded. If None, the function
                will be uploaded to the global scope. Defaults to None.

        Returns:
            str: The UUID of the uploaded slicing function.
        """

        # Upload dependencies and prevent cycle/multiple upload
        uploaded_dependencies = uploaded_dependencies or set()
        uploaded_dependencies.add(self)
        for dependency in self.dependencies:
            if dependency not in uploaded_dependencies:
                dependency.upload(client, project_key, uploaded_dependencies)

        name = self._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / self.meta.uuid

        if not local_dir.exists():
            os.makedirs(local_dir)
        self.save(local_dir)
        logger.debug(f"Saved {name}.{self.meta.uuid}")

        client.log_artifacts(local_dir, posixpath.join(project_key or "global", self._get_name(), self.meta.uuid))
        self.meta = client.save_meta(self._get_meta_endpoint(self.meta.uuid, project_key), self.meta)

        return self.meta.uuid

    @classmethod
    def download(cls, uuid: str, client: Optional[GiskardClient], project_key: Optional[str]) -> "Artifact":
        """
        Downloads the artifact from the Giskard hub or retrieves it from the local cache.

        Args:
            uuid (str): The UUID of the artifact to download.
            client (GiskardClient, optional): The Giskard client instance used for communication with the hub. If None,
                the artifact will be retrieved from the local cache if available. Defaults to None.
            project_key (str, optional): The project key where the artifact is located. If None, the artifact will be
                retrieved from the global scope. Defaults to None.

        Returns:
            Artifact: The downloaded artifact.

        Raises:
            AssertionError: If the artifact metadata cannot be retrieved.
            AssertionError: If the artifact is not found in the cache and the Giskard client is None.
        """
        name = cls._get_name()

        local_dir = settings.home_dir / settings.cache_dir / (project_key or "global") / name / uuid

        if client is None:
            meta = cls._load_meta_locally(local_dir, uuid)
        else:
            meta = client.load_meta(cls._get_meta_endpoint(uuid, project_key), cls._get_meta_class())

        assert meta is not None, "Could not retrieve test meta"

        # check cache first
        data = cls.load(local_dir, uuid, meta)

        if data is None:
            assert client is not None, f"Cannot find existing {name} {uuid}"
            client.load_artifact(local_dir, posixpath.join(project_key or "global", name, uuid))
            data = cls.load(local_dir, uuid, meta)

        return data


class RegistryArtifact(Artifact[SMT], ABC):
    def _save_locally(self, local_dir: Path):
        with open(Path(local_dir) / "data.pkl", "wb") as f:
            cloudpickle.dump(self, f, protocol=pickle.DEFAULT_PROTOCOL)

    @classmethod
    def _load_meta_locally(cls, local_dir, uuid: str) -> Optional[SMT]:
        meta = tests_registry.get_test(uuid)

        if meta is not None:
            return meta

        return super()._load_meta_locally(local_dir, uuid)

    @classmethod
    def load(cls, local_dir: Path, uuid: str, meta: SMT):
        _function: Optional["RegistryArtifact"]

        if local_dir.exists():
            with open(local_dir / "data.pkl", "rb") as f:
                _function = cloudpickle.load(f)
        else:
            try:
                func = getattr(sys.modules[meta.module], meta.name)

                if inspect.isclass(func) or hasattr(func, "meta"):
                    _function = func()
                else:
                    _function = cls(func)
                    _function.meta = meta
            except Exception:
                return None

        tests_registry.register(_function.meta)

        return _function
