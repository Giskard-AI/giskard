import inspect
import logging
import traceback
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import List, Any, Union, Dict, Optional, Tuple

from mlflow import MlflowClient

from giskard.client.dtos import TestSuiteDTO, TestInputDTO, SuiteTestDTO
from giskard.client.giskard_client import GiskardClient
from giskard.core.core import TestFunctionMeta
from giskard.datasets.base import Dataset
from giskard.ml_worker.core.savable import Artifact
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.testing.registry.giskard_test import (
    GiskardTest,
    Test,
    GiskardTestMethod,
)
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import (
    TransformationFunction,
)
from giskard.ml_worker.testing.test_result import (
    TestResult,
    TestMessage,
    TestMessageLevel,
)
from giskard.models.base import BaseModel

logger = logging.getLogger(__name__)

suite_input_types: List[type] = [
    Dataset,
    BaseModel,
    str,
    bool,
    int,
    float,
    SlicingFunction,
    TransformationFunction,
]


def parse_function_arguments(client, project_key, function_inputs):
    arguments = dict()

    for value in function_inputs:
        if value["isAlias"]:
            continue
        if value["type"] == "Dataset":
            arguments[value["name"]] = Dataset.download(client, project_key, value["value"], False)
        elif value["type"] == "BaseModel":
            arguments[value["name"]] = BaseModel.download(client, project_key, value["value"])
        elif value["type"] == "SlicingFunction":
            arguments[value["name"]] = SlicingFunction.download(value["value"], client, None)(
                **parse_function_arguments(client, project_key, value["params"])
            )
        elif value["type"] == "TransformationFunction":
            arguments[value["name"]] = TransformationFunction.download(value["value"], client, None)(
                **parse_function_arguments(client, project_key, value["params"])
            )
        elif value["type"] == "float":
            arguments[value["name"]] = float(value["value"])
        elif value["type"] == "int":
            arguments[value["name"]] = int(value["value"])
        elif value["type"] == "str":
            arguments[value["name"]] = str(value["value"])
        elif value["type"] == "bool":
            arguments[value["name"]] = bool(value["value"])
        elif value["type"] == "kwargs":
            kwargs = dict()
            exec(value["value"], {"kwargs": kwargs})
            arguments.update(kwargs)
        else:
            raise IllegalArgumentError("Unknown argument type")
    return arguments


class TestSuiteResult:
    """Represents the result of a test suite."""

    def __init__(self, passed: bool, results: List[Tuple[str, TestResult, Dict[str, Any]]]):
        self.passed = passed
        self.results = results

    def __repr__(self):
        return f"<TestSuiteResult ({'passed' if self.passed else 'failed'})>"

    def _repr_html_(self):
        from ..visualization.widget import TestSuiteResultWidget

        widget = TestSuiteResultWidget(self)
        return widget.render_html()

    def to_mlflow(self, mlflow_client: MlflowClient = None, mlflow_run_id: str = None):
        import mlflow
        from giskard.integrations.mlflow.giskard_evaluator_utils import process_text

        metrics = dict()
        for test_result in self.results:
            test_name = test_result[0]
            test_name = process_text(test_name)
            if mlflow_client is None and mlflow_run_id is None:
                mlflow.log_metric(test_name, test_result[1].metric)
            elif mlflow_client and mlflow_run_id:
                mlflow_client.log_metric(mlflow_run_id, test_name, test_result[1].metric)
            metrics[test_name] = test_result[1].metric

        return metrics

    def to_wandb(self, **kwargs) -> None:
        """Log the test-suite result to the WandB run.

        Log the current test-suite result in a table format to the active WandB run.

        Parameters
        ----------
        **kwargs :
            Additional keyword arguments
            (see https://docs.wandb.ai/ref/python/init) to be added to the active WandB run.
        """
        from giskard.integrations.wandb.wandb_utils import wandb_run, _parse_test_name
        import wandb
        from ..utils.analytics_collector import analytics

        with wandb_run(**kwargs) as run:
            # Log just a test description and a metric.
            columns = ["Metric name", "Data slice", "Metric value", "Passed"]
            try:
                data = [[*_parse_test_name(result[0]), result[1].metric, result[1].passed] for result in self.results]
                analytics.track(
                    "wandb_integration:test_suite",
                    {
                        "wandb_run_id": run.id,
                        "tests_cnt": len(data),
                    },
                )
            except Exception as e:
                analytics.track(
                    "wandb_integration:test_suite:error:unknown",
                    {
                        "wandb_run_id": wandb.run.id,
                        "error": str(e),
                    },
                )
                raise ValueError(
                    "An error occurred while logging the test suite into wandb. "
                    "Please submit the traceback as a GitHub issue in the following "
                    "repository for further assistance: https://github.com/Giskard-AI/giskard."
                ) from e
            run.log({"Test suite results/Test-Suite Results": wandb.Table(columns=columns, data=data)})


class SuiteInput:
    """
    Represents an input parameter for a test suite.

    Attributes:
        name (str): The name of the input parameter.
        type (Any): The type of the input parameter.

    Raises:
        AssertionError: If the input type is not supported.

    Example:
        >>> input_param = SuiteInput("age", int)
        >>> input_param.name
        'age'
        >>> input_param.type
        <class 'int'>
    """

    type: Any
    name: str

    def __init__(self, name: str, ptype: Any) -> None:
        assert ptype in suite_input_types, f"Type should be one of these: {suite_input_types}"
        self.name = name
        self.type = ptype


class DatasetInput(SuiteInput):
    """
    Represents a dataset input parameter for a test suite.

    Inherits from `SuiteInput`.

    Attributes:
        name (str): The name of the dataset input parameter.
        target (Optional[str]): The target column of the dataset.

    Example:
        >>> dataset_input = DatasetInput("data", target="label")
        >>> dataset_input.name
        'data'
        >>> dataset_input.type
        <class 'Dataset'>
        >>> dataset_input.target
        'label'
    """

    target: Optional[str] = None

    def __init__(self, name: str, target: Optional[str] = None) -> None:
        super().__init__(name, Dataset)
        self.target = target


class ModelInput(SuiteInput):
    """
    Represents a model input parameter for a test suite.

    Inherits from `SuiteInput`.

    Attributes:
        name (str): The name of the model input parameter.
        model_type (Optional[str]): The type or name of the model.

    Example:
        >>> model_input = ModelInput("model", model_type="SKLearnModel")
        >>> model_input.name
        'model'
        >>> model_input.model_type
        'SKLearnModel'
    """

    model_type: Optional[str] = None

    def __init__(self, name: str, model_type: Optional[str] = None) -> None:
        super().__init__(name, BaseModel)
        self.model_type = model_type


@dataclass
class TestPartial:
    giskard_test: GiskardTest
    provided_inputs: Dict[str, Any]
    test_name: Union[int, str]


def single_binary_result(test_results: List):
    return all(res.passed for res in test_results)


def build_test_input_dto(client, p, pname, ptype, project_key, uploaded_uuids):
    if issubclass(type(p), Dataset) or issubclass(type(p), BaseModel):
        if str(p.id) not in uploaded_uuids:
            p.upload(client, project_key)
        uploaded_uuids.append(str(p.id))
        return TestInputDTO(name=pname, value=str(p.id), type=ptype)
    elif issubclass(type(p), Artifact):
        if str(p.meta.uuid) not in uploaded_uuids:
            p.upload(client)
        uploaded_uuids.append(str(p.meta.uuid))
        return TestInputDTO(
            name=pname,
            value=str(p.meta.uuid),
            type=ptype,
            params=[
                build_test_input_dto(
                    client,
                    value,
                    pname,
                    p.meta.args[pname].type,
                    project_key,
                    uploaded_uuids,
                )
                for pname, value in p.params.items()
            ],
        )
    elif isinstance(p, SuiteInput):
        return TestInputDTO(name=pname, value=p.name, is_alias=True, type=ptype)
    else:
        return TestInputDTO(name=pname, value=str(p), type=ptype)


def _generate_test_partial(test_fn: Test, test_name: Optional[Union[int, str]] = None, **params) -> TestPartial:
    if isinstance(test_fn, GiskardTestMethod):
        actual_params = {k: v for k, v in test_fn.params.items() if v is not None}
    elif isinstance(test_fn, GiskardTest):
        actual_params = {
            k: test_fn.__dict__[k]
            for k, v in inspect.signature(test_fn.__init__).parameters.items()
            if test_fn.__dict__[k] is not None
        }
    else:
        actual_params = dict()
        test_fn = GiskardTestMethod(test_fn)

    actual_params.update(params)

    if test_name is None:
        test_name = test_fn.meta.name if test_fn.meta.display_name is None else test_fn.meta.display_name

    return TestPartial(test_fn, actual_params, test_name)


class Suite:
    """
    A class representing a test suite that groups a collection of test cases together. The Suite class provides
    methods to add new tests, execute all tests, and save the suite to a Giskard instance.

    Attributes:
        id : int
            An integer identifying the suite.
        tests : List[TestPartial]
            A list of TestPartial objects representing the test cases in the suite.
            A mapping of suite parameters with their corresponding SuiteInput objects.
        name : str
            A string representing the name of the suite.
    """

    id: int
    tests: List[TestPartial]
    name: str

    def __init__(self, name=None) -> None:
        """Create a new Test Suite instance with a given name.

        Parameters
        ----------
        name : str, optional
            The name of the test suite.
        """
        self.tests = list()
        self.name = name

    def run(self, verbose: bool = True, **suite_run_args):
        """Execute all the tests that have been added to the test suite through the `add_test` method.

        Parameters
        ----------
        verbose : bool
            If set to `True`, the execution information for each test will be displayed. Defaults to `False`.
        **suite_run_args : dict, optional
            Any arguments passed here will be applied to all the tests in the suite whenever they match with the
            arguments defined for each test. If a test contains an argument that has already been defined, it will not
            get overridden. If any inputs on the test suite are missing, an error will be raised.

        Returns
        -------
        TestSuiteResult
            containing test execution information
        """
        results: List[(str, TestResult, Dict[str, Any])] = list()
        required_params = self.find_required_params()
        undefined_params = {k: v for k, v in required_params.items() if k not in suite_run_args}
        if len(undefined_params):
            raise ValueError(f"Missing {len(undefined_params)} required parameters: {undefined_params}")

        for test_partial in self.tests:
            test_params = self.create_test_params(test_partial, suite_run_args)

            try:
                result = test_partial.giskard_test.get_builder()(**test_params).execute()

                if isinstance(result, bool):
                    result = TestResult(passed=result)

                results.append((test_partial.test_name, result, test_params))
                if verbose:
                    print(
                        """Executed '{0}' with arguments {1}: {2}""".format(test_partial.test_name, test_params, result)
                    )
            except BaseException:  # noqa NOSONAR
                error = traceback.format_exc()
                logging.exception(f"An error happened during test execution for test: {test_partial.test_name}")
                results.append(
                    (
                        test_partial.test_name,
                        TestResult(
                            passed=False,
                            is_error=True,
                            messages=[TestMessage(type=TestMessageLevel.ERROR, text=error)],
                        ),
                        test_params,
                    )
                )

        passed = single_binary_result([result for name, result, params in results])

        logger.info(f"Executed test suite '{self.name or 'unnamed'}'")
        logger.info(f"result: {'success' if passed else 'failed'}")
        for test_name, r, params in results:
            logger.info(f"{test_name} ({params}): {format_test_result(r)}")

        return TestSuiteResult(passed, results)

    @staticmethod
    def create_test_params(test_partial, kwargs):
        if isinstance(test_partial.giskard_test, GiskardTestMethod):
            available_params = inspect.signature(test_partial.giskard_test.test_fn).parameters.items()
        else:
            available_params = inspect.signature(test_partial.giskard_test.__init__).parameters.items()

        test_params = {}
        for pname, p in available_params:
            if pname in kwargs:
                test_params[pname] = kwargs[pname]
            elif pname in test_partial.provided_inputs:
                if isinstance(test_partial.provided_inputs[pname], SuiteInput):
                    test_params[pname] = kwargs[test_partial.provided_inputs[pname].name]
                else:
                    test_params[pname] = test_partial.provided_inputs[pname]
        return test_params

    def upload(self, client: GiskardClient, project_key: str):
        """
        Saves the test suite to the Giskard backend and sets its ID.

        :param client: A GiskardClient instance to connect to the backend.
        :param project_key: The key of the project that the test suite belongs to.
        :return: The current instance of the test Suite to allow chained call.
        """
        if self.name is None:
            self.name = "Unnamed test suite"
        self.id = client.save_test_suite(self.to_dto(client, project_key))
        project_id = client.get_project(project_key).project_id
        print(f"Test suite has been saved: {client.host_url}/main/projects/{project_id}/test-suite/{self.id}/overview")
        return self

    def to_dto(self, client: GiskardClient, project_key: str):
        suite_tests: List[SuiteTestDTO] = list()

        # Avoid to upload the same artifacts several times
        uploaded_uuids: List[str] = []

        for t in self.tests:
            suite_tests.append(
                SuiteTestDTO(
                    testUuid=t.giskard_test.upload(client),
                    functionInputs={
                        pname: build_test_input_dto(
                            client,
                            p,
                            pname,
                            t.giskard_test.meta.args[pname].type,
                            project_key,
                            uploaded_uuids,
                        )
                        for pname, p in t.provided_inputs.items()
                    },
                )
            )

        return TestSuiteDTO(name=self.name, project_key=project_key, tests=suite_tests)

    def add_test(self, test_fn: Test, test_name: Optional[Union[int, str]] = None, **params) -> "Suite":
        """
        Add a test to the suite.

        Args:
            test_fn (Test): A test method that will be executed or an instance of a GiskardTest class.
            test_name (Optional[Union[int, str]], optional): A unique identifier used to track the test result.
                If None, the identifier will be generated based on the module and name of the test method.
                If the identifier already exists in the suite, a new unique identifier will be generated.
            **params: Default parameters to be passed to the test method.
                This parameter will be ignored if `test_fn` is an instance of GiskardTest.

        Returns:
            Suite: The current instance of the test suite to allow chained calls.

        """
        self.tests.append(_generate_test_partial(test_fn, test_name, **params))

        return self

    @singledispatchmethod
    def remove_test(self, arg):
        """
        Remove a test from the suite.

        Args:
            arg (int|str|GiskardTest):
                If int: remove the test by index.
                If str: remove the test by name passed during the add_test method
                If GiskardTest: remove the test(s) by reference

        Returns:
            Suite: The current instance of the test suite to allow chained calls.

        """
        raise NotImplementedError("To remove a test from the suite please pass its index, its name or its reference")

    @remove_test.register
    def _remove_test_by_idx(self, idx: int):
        self.tests.pop(idx)
        return self

    @remove_test.register
    def _remove_test_by_name(self, test_name: str):
        self.tests = [test for test in self.tests if test.test_name != test_name]
        return self

    @remove_test.register
    def _remove_test_by_reference(self, giskard_test: GiskardTest):
        self.tests = [test for test in self.tests if test.giskard_test.meta.uuid != giskard_test.meta.uuid]
        return self

    def update_test_params(self, index: int, **params):
        """
        Update a test from the suite.

        Args:
            index (int): The index of the test to be updated
            **params: The params to be added/updated to the current one

        Returns:
            Suite: The current instance of the test suite to allow chained calls.

        """
        test = self.tests[index]
        inputs = test.provided_inputs.copy()
        inputs.update(**params)
        self.tests[index] = _generate_test_partial(test.giskard_test, test.test_name, **inputs)

        return self

    def find_required_params(self):
        res = dict()

        for test_partial in self.tests:
            if isinstance(test_partial.giskard_test, GiskardTestMethod):
                available_params = inspect.signature(test_partial.giskard_test.test_fn).parameters.values()
            else:
                available_params = inspect.signature(test_partial.giskard_test.__init__).parameters.values()

            for p in available_params:
                if p.default == inspect.Signature.empty:
                    if p.name not in test_partial.provided_inputs:
                        res[p.name] = p.annotation
                    elif isinstance(test_partial.provided_inputs[p.name], SuiteInput):
                        if test_partial.provided_inputs[p.name].type != p.annotation:
                            raise ValueError(
                                f"Test {test_partial.giskard_test.func.__name__} requires {p.name} input to "
                                f"be {p.annotation.__name__} "
                                f"but {test_partial.provided_inputs[p.name].type.__name__} was provided"
                            )
                        res[test_partial.provided_inputs[p.name].name] = p.annotation
        return res

    def generate_tests(self, inputs: List[SuiteInput]):
        giskard_tests = [
            test
            for test in tests_registry.get_all().values()
            if contains_tag(test, "giskard") and not self._contains_test(test)
        ]

        for test in giskard_tests:
            self._add_test_if_suitable(test, inputs)

        return self

    def _add_test_if_suitable(self, test_func: TestFunctionMeta, inputs: List[SuiteInput]):
        required_args = [arg for arg in test_func.args.values() if arg.default is None]
        input_dict: Dict[str, SuiteInput] = {i.name: i for i in inputs}

        if any(
            [
                arg
                for arg in required_args
                if arg.name not in input_dict or arg.type != input_dict[arg.name].type.__name__
            ]
        ):
            # Test is not added if an input  without default value is not specified
            # or if an input does not match the required type
            return

        suite_args = {}

        for arg in [arg for arg in test_func.args.values() if arg.default is not None and arg.name not in input_dict]:
            # Set default value if not provided
            suite_args[arg.name] = arg.default

        models = [
            modelInput
            for modelInput in input_dict.values()
            if isinstance(modelInput, ModelInput) and modelInput.model_type is not None and modelInput.model_type != ""
        ]
        if any(models) and not contains_tag(test_func, next(iter(models)).model_type):
            return

        if contains_tag(test_func, "ground_truth") and any(
            [
                dataset
                for dataset in input_dict.values()
                if isinstance(dataset, DatasetInput) and dataset.target is None and dataset.target != ""
            ]
        ):
            return

        self.add_test(GiskardTest.download(test_func.uuid, None, None).get_builder()(**suite_args))

    def _contains_test(self, test: TestFunctionMeta):
        return any(t.giskard_test == test for t in self.tests)

    @classmethod
    def download(cls, client: GiskardClient, project_key: str, suite_id: int) -> "Suite":
        suite_json = client.get_suite(client.get_project(project_key).project_id, suite_id)

        suite = Suite(name=suite_json["name"])
        suite.id = suite_id

        for test_json in suite_json["tests"]:
            test = GiskardTest.download(test_json["testUuid"], client, None)
            test_arguments = parse_function_arguments(client, project_key, test_json["functionInputs"].values())
            suite.add_test(test.get_builder()(**test_arguments))

        return suite


def contains_tag(func: TestFunctionMeta, tag: str):
    return any([t for t in func.tags if t.upper() == tag.upper()])


def format_test_result(result: Union[bool, TestResult]) -> str:
    if isinstance(result, TestResult):
        return f"{{{'passed' if result.passed else 'failed'}, metric={result.metric}}}"
    else:
        return "passed" if result else "failed"
