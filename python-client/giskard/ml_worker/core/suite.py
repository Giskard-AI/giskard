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
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.registry import create_test_function_id, tests_registry, TestFunction, \
    TestFunctionArgument
from ml_worker_pb2 import ArtifactRef

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
            res.append(run_test(test_partial.test_func, test_params))

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
        self.id = client.save_test_suite(self.to_dto(client, project_key))
        return self

    def to_dto(self, client: GiskardClient, project_key: str):
        suite_tests: List[SuiteTestDTO] = list()
        for t in self.tests:
            inputs = {}
            for pname, p in t.provided_inputs.items():
                if issubclass(type(p), Tuple) and p[0] is not None:
                    inputs[pname] = TestInputDTO(name=pname, value=p[0].id)
                elif issubclass(type(p), Tuple) or issubclass(type(p), Dataset) or issubclass(type(p), Model):
                    saved_id = without_artifact_ref(p).save(client, project_key)
                    inputs[pname] = TestInputDTO(name=pname, value=saved_id)
                elif isinstance(p, SuiteInput):
                    inputs[pname] = TestInputDTO(name=pname, value=p.name, is_alias=True)
                else:
                    inputs[pname] = TestInputDTO(name=pname, value=p)

            suite_tests.append(SuiteTestDTO(
                testId=create_test_function_id(t.test_func),
                testInputs=inputs
            ))
        return TestSuiteNewDTO(name=self.name, project_key=project_key, tests=suite_tests)

    def add_test(self, test_fn: Union[Callable[[Any], Union[bool]], GiskardTest], **params):
        """
        Add a test to the Suite
        :param test_fn: A test method that will be executed or an instance of a GiskardTest class
        :param params: default params to be passed to the test method,
          will be ignored if test_fn is an instance of GiskardTest
        :return: The current instance of the test Suite to allow chained call
        """
        if isinstance(test_fn, GiskardTest):
            self.tests.append(TestPartial(type(test_fn), {k: v for k, v in test_fn.__dict__.items() if v is not None}))
        else:
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

    def generate_tests(
            self,
            model: Optional[Union[Model, Tuple[Optional[ArtifactRef], Model]]],
            actual_dataset: Optional[Union[Model, Tuple[Optional[ArtifactRef], Model]]],
            reference_dataset: Optional[Union[Model, Tuple[Optional[ArtifactRef], Model]]],
    ):
        if model is None:
            return self

        model = with_artifact_ref(model)
        actual_dataset = with_artifact_ref(actual_dataset)
        reference_dataset = with_artifact_ref(reference_dataset)

        giskard_tests = [test for test in tests_registry.get_all().values()
                         if contains_tag(test, 'giskard') and not self._contains_test(test)]

        for test in giskard_tests:
            self._add_test_if_suitable(test, model, actual_dataset, reference_dataset)

        return self

    def _add_test_if_suitable(
            self,
            test_func: TestFunction,
            model: Optional[Tuple[Optional[ArtifactRef], Model]],
            actual_dataset: Optional[Tuple[Optional[ArtifactRef], Dataset]],
            reference_dataset: Optional[Tuple[Optional[ArtifactRef], Dataset]]
    ):
        args = {}

        if model is None or not contains_tag(test_func, model[1].meta.model_type.value):
            return

        if contains_tag(test_func, 'ground_truth'):
            if actual_dataset is None or actual_dataset[1].target is None or reference_dataset is None or reference_dataset[1].target:
                return

        for model_arg in test_func.args.values():
            if model_arg.type == 'Model':
                args[model_arg.name] = model

        actual_reference_dataset_arguments = find_actual_reference_dataset_arguments(test_func)
        if actual_reference_dataset_arguments is not None:
            if actual_dataset is None or reference_dataset is None:
                return
            else:
                args[actual_reference_dataset_arguments[0].name] = actual_dataset
                args[actual_reference_dataset_arguments[1].name] = reference_dataset
        elif actual_dataset is not None:
            for model_arg in test_func.args.values():
                if model_arg.type == 'Dataset':
                    args[model_arg.name] = actual_dataset

        self.add_test(test_func.fn, **args)

    def _contains_test(self, test: TestFunction):
        return any(t.test_func == test for t in self.tests)


def find_actual_reference_dataset_arguments(test_func: TestFunction) \
        -> Optional[Tuple[TestFunctionArgument, TestFunctionArgument]]:
    actual_dataset = [arg for arg in test_func.args.values()
                      if match_arg_name_and_type(arg, 'actual_dataset', 'Dataset')]

    reference_dataset = [arg for arg in test_func.args.values()
                         if match_arg_name_and_type(arg, 'reference_dataset', 'Dataset')]

    if len(actual_dataset) == 1 and len(reference_dataset) == 1:
        return actual_dataset[0], reference_dataset[0]
    else:
        return None


def match_arg_name_and_type(arg: TestFunctionArgument, name: str, type: str):
    return arg.name == name and arg.type == type


def contains_tag(func: TestFunction, tag: str):
    return any([t for t in func.tags if t.upper() == tag.upper()])


T = TypeVar('T')


def with_artifact_ref(val: Optional[Union[T, Tuple[Optional[ArtifactRef], T]]]) -> Optional[Tuple[Optional[ArtifactRef], T]]:
    if val is None or isinstance(val, Tuple):
        return val
    else:
        return None, val


def without_artifact_ref(val: Optional[Union[T, Tuple[Optional[ArtifactRef], T]]]) -> Optional[T]:
    if val is None or not isinstance(val, Tuple):
        return val
    else:
        return val[1]
