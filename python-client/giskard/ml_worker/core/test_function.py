import logging

import cloudpickle
import hashlib
import os
import pickle
import posixpath
import sys
from pathlib import Path
from typing import Any

from giskard import test
from giskard.client.giskard_client import GiskardClient
from giskard.core.core import TestFunctionMeta
from giskard.ml_worker.testing.registry.registry import tests_registry, generate_func_id
from giskard.ml_worker.testing.tests.heuristic import test_right_label
from giskard.settings import settings

logger = logging.getLogger(__name__)


class TestFunction:
    func: Any
    meta: TestFunctionMeta

    def __init__(self, func: Any, meta: TestFunctionMeta):
        self.func = func
        self.meta = meta

    @classmethod
    def of(cls, func: Any):
        func_name = f"{func.__module__}.{func.__name__}"

        if func_name.startswith('__main__'):
            reference = cloudpickle.dumps(func)
            func_name += hashlib.sha1(reference).hexdigest()

        func_uuid = generate_func_id(func_name)

        meta = tests_registry.get_test(func_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            test(func)
            meta = tests_registry.get_test(func_uuid)
            print(meta)

        return cls(func, meta)

    def save(self, client: GiskardClient, project_key) -> str:
        if self.meta.version is not None:
            return self.meta.uuid

        if self.meta.module is '__main__':
            local_dir = settings.home_dir / settings.cache_dir / project_key / "tests" / self.meta.uuid

            if not local_dir.exists():
                os.makedirs(local_dir)
                with open(Path(local_dir) / 'giskard-function.pkl', 'wb') as f:
                    cloudpickle.dump(self.func, f)
                    if client is not None:
                        client.log_artifacts(local_dir, posixpath.join(project_key, "tests", self.meta.uuid))

        client.save_test_function_meta(project_key,
                                       self.meta.uuid,
                                       self.meta)

        return self.meta.uuid

    @classmethod
    def load(cls, client: GiskardClient, project_key: str, func_uuid: str):
        meta = tests_registry.get_test(func_uuid)
        if meta is not None:
            return cls(meta.fn, meta)

        meta = client.load_test_function_meta(project_key, func_uuid)

        if meta.module is '__main__':
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            local_dir = settings.home_dir / settings.cache_dir / project_key / "tests" / func_uuid

            if client is None:
                # internal worker case, no token based http client
                assert local_dir.exists(), f"Cannot find existing function {project_key}.{func_uuid}"
            else:
                client.load_artifact(local_dir, posixpath.join(project_key, "tests", meta.uuid))

            with open(Path(local_dir) / 'giskard-function.pkl', 'rb') as f:
                func = pickle.load(f)

        meta.fn = func

        return cls(func, meta)


def test_reg():
    TestFunction.of(test_right_label)
