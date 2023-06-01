import inspect
import pickle
import sys
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Union, Callable, Optional, Type

from giskard.core.core import TestFunctionMeta, SMT
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.core.test_result import TestResult
from giskard.ml_worker.testing.registry.registry import tests_registry, get_object_uuid

Result = Union[TestResult, bool]


class GiskardTest(Savable[Type, TestFunctionMeta], ABC):
    """
    The base class of all Giskard's tests.

    The tests are executed inside the `execute` method. All arguments should be passed in the `__init__` method. It is
    required to set default values for all arguments (either `None` or a default values).
    """

    def __init__(self):
        test_uuid = get_object_uuid(type(self))
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            from giskard import test
            test(type(self))
            meta = tests_registry.get_test(test_uuid)
        super(GiskardTest, self).__init__(type(self), meta)

    @abstractmethod
    def execute(self) -> Result:
        """
        Execute the test
        :return: A TestResult or a bool containing detailed information of the test execution results
        :rtype: Union[TestResult, bool]
        """
        ...

    @classmethod
    def _get_name(cls) -> str:
        return 'tests'

    @classmethod
    def _get_meta_class(cls) -> type(SMT):
        return TestFunctionMeta

    def _get_uuid(self) -> str:
        return get_object_uuid(type(self))

    def _should_save_locally(self) -> bool:
        return self.data.__module__.startswith('__main__')

    def _should_upload(self) -> bool:
        return self.meta.version is None

    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: TestFunctionMeta):
        if not meta.module.startswith('__main__'):
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            if not local_dir.exists():
                return None
            with open(Path(local_dir) / 'data.pkl', 'rb') as f:
                func = pickle.load(f)

        if inspect.isclass(func):
            giskard_test = func()
        else:
            giskard_test = GiskardTestMethod(func)

        tests_registry.add_func(meta)
        giskard_test.meta = meta

        return giskard_test

    @classmethod
    def _read_meta_from_loca_dir(cls, uuid: str, project_key: Optional[str]) -> TestFunctionMeta:
        meta = tests_registry.get_test(uuid)
        assert meta is not None, f"Cannot find test function {uuid}"
        return meta

    def get_builder(self):
        return type(self)


Function = Callable[..., Result]

Test = Union[GiskardTest, Function]


class GiskardTestMethod(GiskardTest):
    params: ...

    def __init__(self, test_fn: Function) -> None:
        self.test_fn = test_fn
        test_uuid = get_object_uuid(test_fn)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            from giskard import test
            test()(test_fn)
            meta = tests_registry.get_test(test_uuid)
        super(GiskardTest, self).__init__(test_fn, meta)

    def __call__(self, *args, **kwargs) -> 'GiskardTestMethod':
        self.is_initialized = True
        self.params = kwargs

        for idx, arg in enumerate(args):
            self.params[next(iter([arg.name for arg in self.meta.args.values() if arg.argOrder == idx]))] = arg

        unknown_params = [param for param in self.params if param not in self.meta.args]
        assert len(unknown_params) == 0, \
            f"The test '{self.meta.name}' doesn't contain any of those parameters: {', '.join(unknown_params)}"

        return self

    def execute(self) -> Result:
        return self.test_fn(**self.params)

    def __repr__(self) -> str:
        if not self.is_initialized:
            hint = "Test object hasn't been initialized, call it by providing the inputs"
        else:
            hint = 'To execute the test call "execute()" method'
        output = [hint]
        if self.params and len(self.params):
            output.append(f"Named inputs: {self.params}")

        return "\n".join(output)

    def get_builder(self):
        return GiskardTestMethod(self.data)
