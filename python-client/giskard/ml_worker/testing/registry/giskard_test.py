import sys
import copy
import pickle
import inspect
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Union, Callable, Optional, Type

from giskard.core.core import TestFunctionMeta, SMT
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.core.test_result import TestResult
from giskard.ml_worker.testing.registry.registry import tests_registry, get_object_uuid
from giskard.ml_worker.testing.registry.utils import is_local_function

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
        return is_local_function(self.data.__module__)

    def _should_upload(self) -> bool:
        return self.meta.version is None

    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: TestFunctionMeta):
        if not is_local_function(meta.module):
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            if not local_dir.exists():
                return None
            with open(Path(local_dir) / 'data.pkl', 'rb') as f:
                func = pickle.load(f)

        if inspect.isclass(func) or hasattr(func, 'meta'):
            giskard_test = func()
        elif isinstance(func, GiskardTest):
            giskard_test = func
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
    def __init__(self, test_fn: Function) -> None:
        self.params = {}
        self.is_initialized = False
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
        instance = copy.deepcopy(self)

        instance.is_initialized = True
        instance.params = kwargs

        for idx, arg in enumerate(args):
            instance.params[next(iter([arg.name for arg in instance.meta.args.values() if arg.argOrder == idx]))] = arg

        return instance

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
