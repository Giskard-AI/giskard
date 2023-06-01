import hashlib
from typing import Union, Callable, Any

import cloudpickle

from giskard import test
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


class GiskardTest(Savable[Any, TestFunctionMeta]):
    """
    The base class of all Giskard's tests

    The test are then executed inside the execute method
    All arguments shall be passed in the __init__ method
    It is advised to set default value for all arguments (None or actual value) in order to allow autocomplete
    """

    def __init__(self):
        test_uuid = get_test_uuid(type(self))
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            test(type(self))
            meta = tests_registry.get_test(test_uuid)
        super(GiskardTest, self).__init__(type(self), meta)

    def set_params(self):
        pass

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
        return self.meta.version is None


Function = Callable[..., Result]

Test = Union[GiskardTest, Function]


class GiskardTestMethod(GiskardTest):
    params: ...

    def __init__(self, test_function: Function):
        test_uuid = get_test_uuid(test_function)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            test(test_function)
            meta = tests_registry.get_test(test_uuid)
        super(GiskardTest, self).__init__(test_function, meta)

    def set_params(self, **kwargs):
        self.params = kwargs

    def execute(self) -> Result:
        return self.data(**self.params)
