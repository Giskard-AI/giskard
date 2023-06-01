import hashlib
from pathlib import Path
from typing import Union, Callable, Any, Optional

import cloudpickle

from giskard import test
from giskard.client.giskard_client import GiskardClient
from giskard.core.core import TestFunctionMeta
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.core.test_result import TestResult
from giskard.ml_worker.testing.registry.registry import tests_registry, generate_func_id

Result = Union[TestResult, bool]


def get_test_uuid(func) -> str:
    func_name = f"{func.__module__}.{func.__name__}"

    if func_name.startswith('__main__'):
        reference = cloudpickle.dumps(func)
        func_name += hashlib.sha1(reference).hexdigest()

    return generate_func_id(func_name)


class GiskardTest(Savable):
    """
    The base class of all Giskard's tests

    The test are then executed inside the execute method
    All arguments shall be passed in the __init__ method
    It is advised to set default value for all arguments (None or actual value) in order to allow autocomplete
    """

    def execute(self) -> Result:
        """
        Execute the test
        :return: A SingleTestResult containing detailed information of the test execution results
        """
        pass

    @classmethod
    def _get_name(cls) -> str:
        return 'tests'

    def _get_uuid(self) -> str:
        return get_test_uuid(type(self))

    def _should_save_locally(self) -> bool:
        func_name = f"{self.__module__}.{self.__name__}"
        return func_name.startswith('__main__')

    def _should_upload(self) -> bool:
        test_uuid = self._get_uuid()
        meta = tests_registry.get_test(test_uuid)
        return meta is None

    def _save_meta(self, client: GiskardClient, project_key: Optional[str] = None):
        test_uuid = self._get_uuid()
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            test(type(self))
            meta = tests_registry.get_test(test_uuid)
        client.save_test_function_meta(meta)

    def _save_to_local_dir(self, local_dir: Path):
        with open(Path(local_dir) / 'giskard-function.pkl', 'wb') as f:
            cloudpickle.dump(type(self), f)


Function = Callable[..., Result]

Test = Union[GiskardTest, Function]


class GiskardTestMethod(GiskardTest):
    test: Function
    params: ...

    def __init__(self, test: Function, **kwargs):
        self.test = test
        self.params = kwargs

    def execute(self) -> Result:
        return self.test(self.params)

    def _get_uuid(self) -> str:
        return get_test_uuid(self.test)

    def _should_save_locally(self) -> bool:
        func_name = f"{self.test.__module__}.{self.test.__name__}"
        return func_name.startswith('__main__')

    def _save_meta(self, client: GiskardClient, project_key: Optional[str] = None):
        test_uuid = self._get_uuid()
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            test(self.test)
            meta = tests_registry.get_test(test_uuid)
        client.save_test_function_meta(meta)

    def _save_to_local_dir(self, local_dir: Path):
        with open(Path(local_dir) / 'giskard-function.pkl', 'wb') as f:
            cloudpickle.dump(self.test, f)


class GiskardTestReference(Savable[Test, TestFunctionMeta]):

    def _should_save_locally(self) -> bool:
        func_name = f"{self.obj.__module__}.{self.obj.__name__}"
        return func_name.startswith('__main__')

    def _save_meta(self, client: GiskardClient, project_key: Optional[str] = None):
        client.save_test_function_meta(self.meta)

    @classmethod
    def of(cls, func: Function):
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
    def _load_meta(cls, func_uuid: str, client: GiskardClient, project_key: Optional[str]) -> TestFunctionMeta:
        meta = tests_registry.get_test(func_uuid)
        if meta is not None:
            return meta

        return client.load_test_function_meta(func_uuid)

    @classmethod
    def _read_from_local_dir(self, local_dir: Path, meta: TestFunctionMeta) -> Any:
        if meta.module is '__main__':
            return getattr(sys.modules[meta.module], meta.name)
        elif not local_dir.exists():
            return None
        else:
            with open(Path(local_dir) / 'giskard-function.pkl', 'rb') as f:
                print(f)
                return pickle.load(f)
