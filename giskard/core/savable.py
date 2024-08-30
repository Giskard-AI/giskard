from typing import Generic, Optional, Set

import inspect
import logging
import posixpath
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import cloudpickle
import yaml

from giskard.core.core import SMT, SavableMeta
from giskard.exceptions.giskard_exception import python_env_exception_helper
from giskard.registry.registry import tests_registry
from giskard.registry.utils import dump_by_value

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
    def _get_meta_endpoint(cls, uuid: str, project_key: str) -> str:
        return posixpath.join("project", project_key, cls._get_name(), uuid)

    def _save_meta_locally(self, local_dir):
        with open(Path(local_dir) / "meta.yaml", "w") as f:
            yaml.dump(self.meta, f)


class RegistryArtifact(Artifact[SMT], ABC):
    def _save_locally(self, local_dir: Path):
        with open(Path(local_dir) / "data.pkl", "wb") as f:
            dump_by_value(self, f)

    @classmethod
    def _load_meta_locally(cls, local_dir, uuid: str) -> Optional[SMT]:
        meta = tests_registry.get_test(uuid)

        if meta is not None:
            return meta

        with open(local_dir / "meta.yaml", "r") as f:
            return yaml.load(f, Loader=yaml.Loader)

    @classmethod
    def load(cls, local_dir: Path, uuid: str, meta: SMT):
        _function: Optional["RegistryArtifact"]

        if local_dir.exists():
            with open(local_dir / "data.pkl", "rb") as f:
                try:
                    # According to https://github.com/cloudpipe/cloudpickle#cloudpickle:
                    # Cloudpickle can only be used to send objects between the exact same version of Python.
                    _function = cloudpickle.load(f)
                except Exception as e:
                    raise python_env_exception_helper(cls.__name__, e)
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
