import cloudpickle
import hashlib
import os
import pickle
import posixpath
import random
import sys
import uuid
from pathlib import Path
from typing import Any

from giskard.client.giskard_client import GiskardClient
from giskard.settings import settings


def generate_func_id(name) -> str:
    rd = random.Random()
    rd.seed(hashlib.sha1(name.encode('utf-8')).hexdigest())
    func_id = str(uuid.UUID(int=rd.getrandbits(128), version=4))
    return str(func_id)


class TestFunction:
    func: Any
    func_name: str

    def __init__(self, func: Any, func_name: str):
        self.func = func
        self.func_name = func_name

    @classmethod
    def of(cls, func: Any):
        func_name = f"{func.__module__}.{func.__name__}"
        print(func_name)

        if func_name.startswith('__main__'):
            reference = cloudpickle.dumps(func)
            func_name += hashlib.sha1(reference).hexdigest()

        return cls(func, func_name)

    def save(self, client: GiskardClient, project_key) -> str:
        if not self.func_name.startswith('__main__'):
            return self.func_name

        func_id = generate_func_id(self.func_name)

        local_dir = settings.home_dir / settings.cache_dir / project_key / "tests" / func_id

        if not local_dir.exists():
            os.makedirs(local_dir)
            with open(Path(local_dir) / 'giskard-function.pkl', 'wb') as f:
                cloudpickle.dump(self.func, f)
                if client is not None:
                    client.log_artifacts(local_dir, posixpath.join(project_key, "tests", func_id))
                    client.save_test_meta(project_key, #TODO
                                           info.model_uuid,
                                           self.meta,
                                           info.flavors['python_function']['python_version'],
                                           get_size(f))

        return self.func_name

    @classmethod
    def load(cls, client: GiskardClient, project_key: str, func_name: str):
        if not func_name.startswith('__main__'):
            [module_name, func_name] = func_name.split('.')
            func = getattr(sys.modules[module_name], func_name)
        else:
            func_id = generate_func_id(func_name)

            local_dir = settings.home_dir / settings.cache_dir / project_key / "tests" / func_id

            if client is None:
                # internal worker case, no token based http client
                assert local_dir.exists(), f"Cannot find existing function {project_key}.{func_id}"
            else:
                client.load_artifact(local_dir, posixpath.join(project_key, "tests", func_id))

            with open(Path(local_dir) / 'giskard-function.pkl', 'rb') as f:
                func = pickle.load(f)

        return cls(func, func_name)

    @classmethod
    def _read_function_from_local_dir(cls, local_path: str):
        with open(local_path, 'rb') as ds_stream:
            return

