import inspect
import logging
from dataclasses import dataclass
from typing import *
from typing import List, Any

from giskard.client.dtos import TestSuiteNewDTO, SuiteTestDTO, TestInputDTO
from giskard.client.giskard_client import GiskardClient
from giskard.core.model import Model
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.core.test_runner import run_test
from giskard.ml_worker.testing.registry.registry import create_test_function_id

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
        elif hasattr(r, 'passed'):
            passed = passed and r.passed
        else:
            logger.error(f"Invalid test result: {r.__class__.__name__}")
            passed = False
    return passed


class Suite:
    id: int
    tests: List[TestPartial]
    suite_params: Mapping[str, SuiteInput]
    name: str

    def __init__(self, name=None) -> None:
        self.suite_params = {}
        self.tests = []
        self.name = name

    def run(self, **suite_run_args):
        res = []
        required_params = self.find_required_params()
        undefined_params = {k: v for k, v in required_params.items() if k not in suite_run_args}
        if len(undefined_params):
            raise ValueError(f"Missing {len(undefined_params)} required parameters: {undefined_params}")

        for test_partial in self.tests:
            test_params = self.create_test_params(test_partial, suite_run_args)
            res.append(run_test(test_partial.test_func, **test_params))

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
        suite_tests: list[SuiteTestDTO] = list()
        for t in self.tests:
            inputs = {}
            for pname, p in t.provided_inputs.items():
                if issubclass(type(p), Dataset) or issubclass(type(p), Model):
                    saved_id = p.save(client, project_key)
                    inputs[pname] = TestInputDTO(name=pname, value=saved_id)
                elif isinstance(p, SuiteInput):
                    inputs[pname] = TestInputDTO(name=pname, value=p.name, is_alias=True)
                else:
                    inputs[pname] = TestInputDTO(name=pname, value=p)

            suite_tests.append(SuiteTestDTO(
                testId=create_test_function_id(t.test_func),
                testInputs=inputs
            ))
        self.id = client.save_test_suite(TestSuiteNewDTO(name=self.name, project_key=project_key, tests=suite_tests))
        return self

    def add_test(self, test_fn: Callable[[Any], Union[bool]], **params):
        self.tests.append(TestPartial(test_fn, params))
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
