import inspect
import logging
from dataclasses import dataclass
from typing import *

from giskard.client.giskard_client import GiskardClient
from giskard.ml_worker.testing.registry.registry import create_test_function_id
from ml_worker_pb2 import SingleTestResult

logger = logging.getLogger(__name__)


class SuiteInput:
    type: Any
    name: str

    def __init__(self, name: str, ptype: Any) -> None:
        self.name = name
        self.type = ptype


@dataclass
class TestPartial:
    test_func: Any
    provided_inputs: Mapping[str, Any]


def single_binary_result(test_results: List):
    passed = True
    for r in test_results:
        if type(r) == bool:
            passed = passed and r
        elif type(r) == SingleTestResult:
            passed = passed and r.passed
        else:
            logger.error(f"Invalid test result: {r.__class__.__name__}")
            passed = False
    return passed


class Suite:
    tests: List[TestPartial]
    suite_params: Mapping[str, SuiteInput]

    def __init__(self) -> None:
        self.suite_params = {}
        self.tests = []

    def run(self, **suite_run_args):
        res = []
        required_params = self.find_required_params()
        undefined_params = {k: v for k, v in required_params.items() if k not in suite_run_args}
        if len(undefined_params):
            raise ValueError(f"Missing required parameters: {undefined_params}")

        for test_partial in self.tests:
            test_params = self.create_test_params(test_partial, suite_run_args)
            res.append(test_partial.test_func(**test_params))

        return single_binary_result(res), res

    @staticmethod
    def create_test_params(test_partial, kwargs):
        test_params = {}
        for pname, p in inspect.signature(test_partial.test_func).parameters.items():
            if pname in test_partial.provided_inputs:
                if isinstance(test_partial.provided_inputs[pname], SuiteInput):
                    test_params[pname] = kwargs[test_partial.provided_inputs[pname].name]
                else:
                    test_params[pname] = test_partial.provided_inputs[pname]
            elif pname in kwargs:
                test_params[pname] = kwargs[pname]
        return test_params

    def save(self, client: GiskardClient, project_key: str):
        for t in self.tests:
            print("Saving", create_test_function_id(t.test_func))
            for pname, p in t.provided_inputs.items():
                print(pname, p)
        return self

    def add_test(self, test_fn: Callable[[Any], Union[bool]], **params):
        # TODO: validate params vs test_fn declared inputs
        self.tests.append(TestPartial(test_fn, params))
        # input_mapping = {}
        # for pname, p in params.items():
        #     if isinstance(p, SuiteInput):
        #         if pname not in self.suite_params:
        #             self.suite_params[p.name] = p
        #         elif self.suite_params[p.name] != p:
        #             raise ValueError(
        #                 f'parameter "{p.name}" is already declared as suite input of type {p.__class__.__name__}')
        #         input_mapping[pname] = p.name
        # for p in inspect.signature(test_fn).parameters.values():
        #     if p.name not in self.suite_params and p.name not in params:
        #         self.suite_params[p.name] = SuiteInput(p.name, p.annotation)
        # # self.params = self.params.union(inspect.signature(test_fn).parameters.keys() - params.keys())
        # self.tests.append(TestPartial(partial(test_fn, **params), input_mapping))
        return self

    def find_required_params(self):
        res = {}
        for test_partial in self.tests:
            for p in inspect.signature(test_partial.test_func).parameters.values():
                if p.default == inspect.Signature.empty:
                    if p.name not in test_partial.provided_inputs:
                        res[p.name] = p.annotation
                    elif isinstance(test_partial.provided_inputs[p.name], SuiteInput):
                        if test_partial.provided_inputs[p.name].type != p.annotation:
                            raise ValueError(
                                f'Test {test_partial.test_func.__name__} requires {p.name} input to '
                                f'be {p.annotation.__name__} '
                                f'but {test_partial.provided_inputs[p.name].type.__name__} was provided')
                        res[test_partial.provided_inputs[p.name].name] = p.annotation
        return res
