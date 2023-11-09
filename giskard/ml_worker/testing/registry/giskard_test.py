from typing import Callable, List, Optional, Set, Union

import copy
import inspect
import pickle
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import cloudpickle

from giskard.core.core import SMT, TestFunctionMeta
from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.core.savable import Artifact
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry
from giskard.ml_worker.testing.test_result import TestResult
from giskard.utils.analytics_collector import analytics

Result = Union[TestResult, bool]


class GiskardTest(Artifact[TestFunctionMeta], ABC):
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
            from giskard.ml_worker.testing.registry.decorators import test

            test(type(self))
            meta = tests_registry.get_test(test_uuid)
        super(GiskardTest, self).__init__(meta)

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
        return "tests"

    @classmethod
    def _get_meta_class(cls) -> type(SMT):
        return TestFunctionMeta

    def _get_uuid(self) -> str:
        return get_object_uuid(type(self))

    def _save_locally(self, local_dir: Path):
        with open(Path(local_dir) / "data.pkl", "wb") as f:
            cloudpickle.dump(type(self), f, protocol=pickle.DEFAULT_PROTOCOL)

    @classmethod
    def _load_meta_locally(cls, local_dir, uuid: str) -> Optional[TestFunctionMeta]:
        meta = tests_registry.get_test(uuid)

        if meta is not None:
            return meta

        return super()._load_meta_locally(local_dir, uuid)

    @classmethod
    def load(cls, local_dir: Path, uuid: str, meta: TestFunctionMeta):
        if local_dir.exists():
            with open(Path(local_dir) / "data.pkl", "rb") as f:
                func = pickle.load(f)
        elif hasattr(sys.modules[meta.module], meta.name):
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            return None

        if inspect.isclass(func) or hasattr(func, "meta"):
            giskard_test = func()
        elif isinstance(func, GiskardTest):
            giskard_test = func
        else:
            giskard_test = GiskardTestMethod(func)

        tests_registry.add_func(meta)
        giskard_test.meta = meta

        return giskard_test

    def get_builder(self):
        return type(self)


Function = Callable[..., Result]

Test = Union[GiskardTest, Function]


class GiskardTestMethod(GiskardTest):
    def __init__(self, test_fn: Function) -> None:
        self.params = {}
        self.is_initialized = False
        self.test_fn = test_fn
        test_uuid = get_object_uuid(self.test_fn)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            # equivalent to adding @test decorator
            from giskard.ml_worker.testing.registry.decorators import test

            test()(test_fn)
            meta = tests_registry.get_test(test_uuid)

        super(GiskardTest, self).__init__(meta)

    def __call__(self, *args, **kwargs) -> "GiskardTestMethod":
        instance = copy.deepcopy(self)

        instance.is_initialized = True
        instance.params = kwargs

        for idx, arg in enumerate(args):
            instance.params[next(iter([arg.name for arg in instance.meta.args.values() if arg.argOrder == idx]))] = arg

        return instance

    @property
    def dependencies(self) -> Set[Artifact]:
        from inspect import Parameter, signature

        parameters: List[Parameter] = list(signature(self.test_fn).parameters.values())

        return set([param.default for param in parameters if isinstance(param.default, Artifact)])

    def execute(self) -> Result:
        analytics.track("test:execute", {"test_name": self.meta.full_name})

        # if params contains debug then we check if test_fn has debug argument
        if "debug" in self.params and "debug" not in list(inspect.signature(self.test_fn).parameters.keys()):
            self.params.pop("debug")

        return configured_validate_arguments(self.test_fn)(**self.params)

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
        return GiskardTestMethod(self.test_fn)

    def _save_locally(self, local_dir: Path):
        with open(Path(local_dir) / "data.pkl", "wb") as f:
            cloudpickle.dump(self.test_fn, f, protocol=pickle.DEFAULT_PROTOCOL)
