import hashlib
import os
import pickle
import posixpath
import random
import uuid
from pathlib import Path
from typing import Any, Optional

import cloudpickle

from client.giskard_client import GiskardClient
from giskard.settings import settings


class FunctionReference:
    func: Any
    func_name: str
    func_id = str
    reference: bytearray

    def __init__(self, func: Any, func_name: str, func_id: Optional[str], reference: bytearray):
        self.func = func
        self.func_name = func_name
        self.func_id = func_id
        self.reference = reference

    @classmethod
    def of(cls, func: Any):
        func_name = f"{func.__module__}.{func.__name__}"
        reference = cloudpickle.dumps(func)

        if func_name.startswith('__main__'):
            func_name += hashlib.sha1(reference).hexdigest()

        # Ensure to always have the same UUID4 according to the function name
        rd = random.Random()
        rd.seed(hashlib.sha1(func_name.encode('utf-8')).hexdigest())
        func_id = uuid.UUID(int=rd.getrandbits(128), version=4)

        return cls(func, func_name, str(func_id), reference)

    def save(self, client: GiskardClient, project_key) -> str:
        local_dir = settings.home_dir / settings.cache_dir / project_key / "functions" / self.func_id

        if not local_dir.exists():
            os.makedirs(local_dir)
            with open(Path(local_dir) / 'giskard-function.pkl', 'wb') as f:
                cloudpickle.dump(self.func, f)
                if client is not None:
                    client.log_artifacts(local_dir, posixpath.join(project_key, "functions", self.func_id))

        return self.func_id

    @classmethod
    def load(cls, client: GiskardClient, project_key: str, func_id: str):
        local_dir = settings.home_dir / settings.cache_dir / project_key / "functions" / func_id

        if client is None:
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing function {project_key}.{func_id}"
        else:
            client.load_artifact(local_dir, posixpath.join(project_key, "functions", func_id))

        with open(Path(local_dir) / 'giskard-function.pkl', 'rb') as f:
            func = pickle.load(f)
            return cls.of(func)

    @classmethod
    def _read_function_from_local_dir(cls, local_path: str):
        with open(local_path, 'rb') as ds_stream:
            return


def test_method():
    tid = FunctionReference.of(test_method).save(None, "test")
    print(FunctionReference.load(None, 'test', tid).reference)

    def test_anonymous():
        print('Anon retrieved successfully')

    anon_id = FunctionReference.of(test_anonymous).save(None, "test")
    anon = FunctionReference.load(None, 'test', anon_id)
    print(anon.reference)
    anon.func()
