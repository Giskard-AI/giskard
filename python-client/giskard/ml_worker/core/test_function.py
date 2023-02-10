import logging

import cloudpickle
import hashlib
import os
import pickle
import posixpath
import sys
from pathlib import Path
from typing import Any, List, Optional

from giskard import test
from giskard.client.giskard_client import GiskardClient
from giskard.core.core import TestFunctionMeta
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.testing.registry.registry import tests_registry, generate_func_id
from giskard.ml_worker.testing.tests.heuristic import test_right_label
from giskard.settings import settings

logger = logging.getLogger(__name__)


class TestFunction(Savable[Any, TestFunctionMeta]):
    func: Any
    meta: TestFunctionMeta

    def __init__(self, func: Any, meta: TestFunctionMeta):
        self.func = func
        self.meta = meta

    def _should_save_locally(self) -> bool:
        func_name = f"{self.func.__module__}.{self.func.__name__}"
        return func_name.startswith('__main__')

    def _save_meta(self, client: GiskardClient, project_key: Optional[str] = None):
        client.save_test_function_meta(self.meta)

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

        return cls(func, meta)

    @classmethod
    def save_all(cls, client: GiskardClient, test_function_metas: List[TestFunctionMeta]):
        client.save_test_function_registry(test_function_metas)

    @classmethod
    def load(cls, client: GiskardClient, func_uuid: str):
        meta = tests_registry.get_test(func_uuid)
        if meta is not None:
            return cls(meta.fn, meta)

        meta = client.load_test_function_meta(func_uuid)

        if meta.module is '__main__':
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            local_dir = settings.home_dir / settings.cache_dir / "global" / "tests" / func_uuid

            if client is None:
                # internal worker case, no token based http client
                assert local_dir.exists(), f"Cannot find existing function {func_uuid}"
            else:
                client.load_artifact(local_dir, posixpath.join("global", "tests", meta.uuid))

            with open(Path(local_dir) / 'giskard-function.pkl', 'rb') as f:
                print(f)
                func = pickle.load(f)

        meta.fn = func

        return cls(func, meta)


def test_reg():
    TestFunction.of(test_right_label)
