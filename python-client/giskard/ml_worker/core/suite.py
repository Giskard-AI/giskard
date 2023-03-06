import inspect
import logging
import uuid
from dataclasses import dataclass
from typing import List, Any, Union, Dict, Mapping, Callable, Optional

from giskard.client.dtos import TestSuiteDTO, TestInputDTO, SuiteTestDTO
from giskard.client.giskard_client import GiskardClient
from giskard.core.model import Model
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.core.test_result import TestResult
from giskard.ml_worker.core.test_runner import run_test
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.registry import create_test_function_id, tests_registry, TestFunction

logger = logging.getLogger(__name__)

suite_input_types: List[type] = [Dataset, Model, str, bool, int, float]


class SuiteInput:
    type: Any
    name: str

    def __init__(self, name: str, ptype: Any) -> None:
        if type not in suite_input_types:
            assert f'Type should be one of those: {suite_input_types}'
        self.name = name
        self.type = ptype


class DatasetInput(SuiteInput):
    target: Optional[str] = None

    def __init__(self, name: str, target: Optional[str] = None) -> None:
        super().__init__(name, Dataset)
        self.target = target


class ModelInput(SuiteInput):
    model_type: Optional[str] = None

    def __init__(self, name: str, model_type: Optional[str] = None) -> None:
        super().__init__(name, Model)
        self.model_type = model_type


@dataclass
class TestPartial:
    test_func: Any
    provided_inputs: Mapping[str, Any]
    test_identifier: Union[int, str]


def single_binary_result(test_results: List):
    passed = True
    for r in test_results:
        if type(r) == bool:
            passed = passed and r
        elif hasattr(r, "passed"):
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
        res: Dict[str, Union[bool, TestResult]] = dict()
        required_params = self.find_required_params()
        undefined_params = {k: v for k, v in required_params.items() if k not in suite_run_args}
        if len(undefined_params):
            raise ValueError(f"Missing {len(undefined_params)} required parameters: {undefined_params}")

        for test_partial in self.tests:
            test_params = self.create_test_params(test_partial, suite_run_args)
            res[test_partial.test_identifier] = run_test(test_partial.test_func, test_params)

        result = single_binary_result(list(res.values()))

        logger.info(f"Executed test suite '{self.name or 'unnamed'}'")
        logger.info(f"result: {'success' if result else 'failed'}")
        for (test_name, r) in res.items():
            logger.info(f"{test_name}: {format_test_result(r)}")
        return result, res

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

        # Avoid to upload the same artifacts several times
        uploaded_uuids: List[str] = []

        for t in self.tests:
            inputs = {}
            for pname, p in t.provided_inputs.items():
                if issubclass(type(p), Dataset):
                    if str(p.id) not in uploaded_uuids:
                        p.save(client, project_key)
                        uploaded_uuids.append(str(p.id))

                    inputs[pname] = TestInputDTO(name=pname, value=str(p.id))
                if issubclass(type(p), Model):
                    if str(p.id) not in uploaded_uuids:
                        p.upload(client, project_key)
                        uploaded_uuids.append(str(p.id))

                    inputs[pname] = TestInputDTO(name=pname, value=str(p.id))
                elif isinstance(p, SuiteInput):
                    inputs[pname] = TestInputDTO(name=pname, value=p.name, is_alias=True)
                else:
                    inputs[pname] = TestInputDTO(name=pname, value=str(p))

            suite_tests.append(SuiteTestDTO(testId=create_test_function_id(t.test_func), testInputs=inputs))
        return TestSuiteDTO(name=self.name, project_key=project_key, tests=suite_tests)

    def add_test(self, test_fn: Union[Callable[[Any], Union[bool]], GiskardTest],
                 test_identifier: Optional[Union[int, str]] = None, **params):
        """
        Add a test to the Suite
        :param test_fn: A test method that will be executed or an instance of a GiskardTest class
        :param test_identifier: A unique test identifier used to track the test result
        :param params: default params to be passed to the test method,
          will be ignored if test_fn is an instance of GiskardTest
        :return: The current instance of the test Suite to allow chained call
        """
        if isinstance(test_fn, GiskardTest):
            params = {k: v for k, v in test_fn.__dict__.items() if v is not None}
            test_fn = type(test_fn)

        if test_identifier is None:
            test_identifier = f"{test_fn.__module__}.{test_fn.__name__}"
            if any([test for test in self.tests if test.test_identifier == test_identifier]):
                test_identifier = f"{test_identifier}-{str(uuid.uuid4())}"
        elif any([test for test in self.tests if test.test_identifier == test_identifier]):
            assert f"The test identifier {test_identifier} as already been assigned to a test"

        self.tests.append(TestPartial(test_fn, params, test_identifier))

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
                                f"Test {test_partial.test_func.__name__} requires {p.name} input to "
                                f"be {p.annotation.__name__} "
                                f"but {test_partial.provided_inputs[p.name].type.__name__} was provided"
                            )
                        res[test_partial.provided_inputs[p.name].name] = p.annotation
        return res

    def generate_tests(self, inputs: List[SuiteInput]):
        giskard_tests = [test for test in tests_registry.get_all().values()
                         if contains_tag(test, 'giskard') and not self._contains_test(test)]

        for test in giskard_tests:
            self._add_test_if_suitable(test, inputs)

        return self

    def _add_test_if_suitable(self, test_func: TestFunction, inputs: List[SuiteInput]):
        required_args = [arg for arg in test_func.args.values() if arg.default is None]
        input_dict: Dict[str, SuiteInput] = {
            i.name: i
            for i in inputs
        }

        if any([arg for arg in required_args if
                arg.name not in input_dict or not arg.type == input_dict[arg.name].type.__name__]):
            # Test is not added if an input  without default value is not specified
            # or if an input does not match the required type
            return

        suite_args = {}

        for arg in [arg for arg in test_func.args.values() if arg.default is not None and arg.name not in input_dict]:
            # Set default value if not provided
            suite_args[arg.name] = arg.default

        models = [modelInput for modelInput in input_dict.values() if
                  isinstance(modelInput, ModelInput)
                  and modelInput.model_type is not None and modelInput.model_type != ""]
        if any(models) and not contains_tag(test_func, next(iter(models)).model_type):
            return

        if contains_tag(test_func, 'ground_truth') \
                and any([dataset for dataset in input_dict.values()
                         if isinstance(dataset, DatasetInput) and dataset.target is None and dataset.target != ""]):
            return

        self.add_test(test_func.fn, **suite_args)

    def _contains_test(self, test: TestFunction):
        return any(t.test_func == test for t in self.tests)


def contains_tag(func: TestFunction, tag: str):
    return any([t for t in func.tags if t.upper() == tag.upper()])


def format_test_result(result: Union[bool, TestResult]) -> str:
    if isinstance(result, TestResult):
        return f"{{{'passed' if result.passed else 'failed'}, metric={result.metric}}}"
    else:
        return "passed" if result else "failed"
