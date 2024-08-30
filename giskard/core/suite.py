from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

import inspect
import json
import logging
import traceback
import warnings
from dataclasses import dataclass
from datetime import datetime
from functools import singledispatchmethod
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from giskard.core.core import TestFunctionMeta
from giskard.core.errors import GiskardImportError
from giskard.core.savable import Artifact
from giskard.core.test_result import TestMessage, TestMessageLevel, TestResult
from giskard.datasets.base import Dataset
from giskard.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.models.base import BaseModel
from giskard.registry.giskard_test import GiskardTest, GiskardTestMethod, Test
from giskard.registry.registry import tests_registry
from giskard.registry.slicing_function import SlicingFunction
from giskard.registry.transformation_function import TransformationFunction

from ..client.python_utils import warning
from ..utils.analytics_collector import analytics
from ..utils.artifacts import serialize_parameter
from .kwargs_utils import get_imports_code

if TYPE_CHECKING:
    from mlflow import MlflowClient

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


def _parse_function_arguments(folder: Path, function_inputs: List[Dict[str, Any]]):
    arguments = dict()

    for value in function_inputs:
        if value.get("isAlias", False) or value.get("isDefaultValue", False):
            continue
        if value["type"] == "Dataset":
            arguments[value["name"]] = Dataset.load(folder / value["value"])
        elif value["type"] == "BaseModel":
            arguments[value["name"]] = BaseModel.load(folder / value["value"])
        elif value["type"] == "SlicingFunction":
            sf_uuid = value["value"]
            sf_folder = folder / sf_uuid
            arguments[value["name"]] = SlicingFunction.load(
                sf_folder, sf_uuid, SlicingFunction._load_meta_locally(sf_folder, sf_uuid)
            )(**_parse_function_arguments(folder, value["params"]))
        elif value["type"] == "TransformationFunction":
            tf_uuid = value["value"]
            tf_folder = folder / tf_uuid
            arguments[value["name"]] = TransformationFunction.load(
                tf_folder, tf_uuid, TransformationFunction._load_meta_locally(tf_folder, tf_uuid)
            )(**_parse_function_arguments(folder, value["params"]))
        elif value["type"] == "float":
            arguments[value["name"]] = float(value["value"])
        elif value["type"] == "int":
            arguments[value["name"]] = int(value["value"])
        elif value["type"] == "str":
            arguments[value["name"]] = str(value["value"])
        elif value["type"] == "bool":
            arguments[value["name"]] = bool(value["value"])
        elif value["type"] == "Kwargs":
            kwargs = dict()
            exec(value["value"], {"kwargs": kwargs})
            arguments.update(kwargs)
        else:
            raise IllegalArgumentError(f"Unknown argument type: {value['type']}")
    return arguments


TestName = str
TestParams = Dict[str, Any]


@dataclass
class SuiteResult:
    test_name: TestName
    result: TestResult
    params: TestParams
    # Configuration of the test inside the Suite
    test_partial: "TestPartial"

    @property
    def _tuple(self):
        # Method to ensure backward compatibility
        return (self.test_name, self.result, self.params)

    def __getitem__(self, i):
        warnings.warn(
            "The test results has been changed to a class, getting attribute by index will be removed in the future.",
            category=DeprecationWarning,
        )
        return self._tuple[i]

    def __iter__(self):
        warnings.warn(
            "The test results has been changed to a class, the iterator function will be removed in the future..",
            category=DeprecationWarning,
        )
        return self._tuple.__iter__()


class TestSuiteResult:
    """Represents the result of a test suite."""

    suite: "Suite"
    inputs: Dict[str, Any]
    passed: bool
    results: List[SuiteResult]
    execution_date: datetime
    completion_date: datetime

    def __init__(
        self,
        suite: "Suite",
        inputs: Dict[str, Any],
        passed: bool,
        results: List[SuiteResult],
        execution_date: datetime,
        completion_date: datetime,
    ):
        self.suite = suite
        self.inputs = inputs
        self.passed = passed
        self.results = results
        self.execution_date = execution_date
        self.completion_date = completion_date

    def __repr__(self):
        return f"<TestSuiteResult ({'passed' if self.passed else 'failed'})>"

    def _repr_html_(self):
        from ..visualization.widget import TestSuiteResultWidget

        widget = TestSuiteResultWidget(self)
        return widget.render_html()

    def to_json(self, filename=None):
        results = {}
        for suite_result in self.results:
            results[suite_result.test_name] = {
                "result": "Passed" if suite_result.result.passed else "Failed",
                "metric_value": suite_result.result.metric,
            }
        if filename is not None:
            with open(filename, "w") as json_file:
                json.dump(results, json_file, indent=4)
        else:
            return json.dumps(results, indent=4)

    def to_mlflow(self, mlflow_client: MlflowClient = None, mlflow_run_id: str = None):
        import mlflow

        from giskard.integrations.mlflow.giskard_evaluator_utils import process_text

        metrics = dict()
        for test_result in self.results:
            test_name = process_text(test_result.test_name)
            metric_name = process_text(test_result.result.metric_name)
            result = test_result.result
            # TODO: Improve this in GSK-2041
            mlflow_metric_name = test_name if metric_name == "Metric" else f"{metric_name} for {test_name}"
            if mlflow_client is None and mlflow_run_id is None:
                mlflow.log_metric(mlflow_metric_name, result.metric)
            elif mlflow_client and mlflow_run_id:
                mlflow_client.log_metric(mlflow_run_id, mlflow_metric_name, result.metric)
            metrics[mlflow_metric_name] = result.metric

        return metrics

    def to_wandb(self, run: Optional["wandb.wandb_sdk.wandb_run.Run"] = None) -> None:  # noqa
        """Log the test-suite result to the WandB run.

        Log the current test-suite result in a table format to the active WandB run.

        Parameters
        ----------
        run : Optional["wandb.wandb_sdk.wandb_run.Run"]
            WandB run. (Default value = None)

        """
        try:
            import wandb  # noqa
        except ImportError as e:
            raise GiskardImportError("wandb") from e
        from ..integrations.wandb.wandb_utils import _parse_test_name, get_wandb_run

        run = get_wandb_run(run)
        # Log just a test description and a metric.
        columns = ["Metric name", "Data slice", "Metric value", "Passed"]
        try:
            data = [
                [*_parse_test_name(test_result.test_name), test_result.result.metric, test_result.result.passed]
                for test_result in self.results
            ]
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
            raise RuntimeError(
                "An error occurred while logging the test suite into wandb. "
                "Please submit the traceback as a GitHub issue in the following "
                "repository for further assistance: https://github.com/Giskard-AI/giskard."
            ) from e
        run.log({"Test suite results/Test-Suite Results": wandb.Table(columns=columns, data=data)})

    def to_junit(self):
        """Convert the test suite result to JUnit XML format."""
        testsuites = Element("testsuites", {"tests": str(len(self.results))})

        for test_result in self.results:
            test_name, result = test_result.test_name, test_result.result
            testsuite = SubElement(
                testsuites,
                "testsuite",
                {
                    "name": f"Test {test_name} (metric={result.metric})",
                },
            )
            testcase = SubElement(
                testsuite, "testcase", {"name": result.metric_name, "time": str(result.metric)}
            )  # replace with actual time

            if not result.passed:
                failure = SubElement(
                    testcase,
                    "failure",
                    {
                        "message": f"Test failed with metric of {result.metric}",
                        "type": "TestFailed" if not result.is_error else "Error",
                    },
                )
                # Add full test result information here
                for k, v in result.__dict__.items():
                    if k != "messages" and k != "is_error":
                        SubElement(failure, "detail", {"name": k, "value": str(v)})
                for message in result.messages:
                    SubElement(failure, "detail", {"name": "message", "value": message})
            else:
                # Add test result information here
                for k, v in result.__dict__.items():
                    if k != "messages" and k != "is_error":
                        SubElement(testcase, "detail", {"name": k, "value": str(v)})
                for message in result.messages:
                    SubElement(testcase, "detail", {"name": "message", "value": message})

        # Convert to string
        xml_str = minidom.parseString(tostring(testsuites)).toprettyxml(indent="   ")
        return xml_str


class SuiteInput:
    """Represents an input parameter for a test suite.

    Raises
    ------
    AssertionError
        If the input type is not supported.

    Examples
    --------
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
    """Represents a dataset input parameter for a test suite.

    Examples
    --------
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
    """Represents a model input parameter for a test suite.

    Examples
    --------
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
    test_id: Union[int, str]
    display_name: Optional[str] = None
    suite_test_id: Optional[int] = None

    def _to_json(self, folder: Path, saved_uuid_status: Dict[str, bool]):
        params = dict(
            {
                pname: _build_test_input_json(
                    folder,
                    p,
                    pname,
                    self.giskard_test.meta.args[pname].type,
                    saved_uuid_status,
                )
                for pname, p in self.provided_inputs.items()
                if pname in self.giskard_test.meta.args
            }
        )

        kwargs_params = [
            f"{get_imports_code(value)}\nkwargs[{repr(pname)}] = {repr(value)}"
            for pname, value in self.provided_inputs.items()
            if pname not in self.giskard_test.meta.args
        ]
        if len(kwargs_params) > 0:
            params["kwargs"] = {"name": "kwargs", "value": "\n".join(kwargs_params), "type": "Kwargs"}

        if self.giskard_test.meta.uuid not in saved_uuid_status:
            test_folder = folder / str(self.giskard_test.meta.uuid)
            test_folder.mkdir(exist_ok=True)
            self.giskard_test.save(test_folder)

        return {
            "id": self.suite_test_id,
            "testUuid": str(self.giskard_test.meta.uuid),
            "functionInputs": params,
            "displayName": self.display_name,
        }


def single_binary_result(test_results: List):
    return all(res.passed for res in test_results)


def _build_test_input_json(folder, p, pname, ptype, uploaded_uuid_status: Dict[str, bool]):
    if issubclass(type(p), Dataset) or issubclass(type(p), BaseModel):
        if _try_save_artifact(p, folder, uploaded_uuid_status):
            return {"name": pname, "value": str(p.id), "type": ptype}
        else:
            return {"name": pname, "value": pname, "is_alias": True, "type": ptype}
    elif issubclass(type(p), Artifact):
        if not _try_save_artifact(p, folder, uploaded_uuid_status):
            return {"name": pname, "value": pname, "is_alias": True, "type": ptype}

        kwargs_params = [
            f"kwargs[{pname}] = {repr(value)}" for pname, value in p.params.items() if pname not in p.meta.args
        ]
        kwargs_param = (
            [] if len(kwargs_params) == 0 else [{"name": "kwargs", "value": "\n".join(kwargs_params), "type": "Kwargs"}]
        )

        return {
            "name": pname,
            "value": str(p.meta.uuid),
            "type": ptype,
            "params": [
                _build_test_input_json(
                    folder,
                    value,
                    pname,
                    p.meta.args[pname].type,
                    uploaded_uuid_status,
                )
                for pname, value in p.params.items()
                if pname in p.meta.args
            ]
            + kwargs_param,
        }
    elif isinstance(p, SuiteInput):
        return {"name": pname, "value": p.name, "is_alias": True, "type": ptype}
    else:
        return {"name": pname, "value": str(p), "type": ptype}


def generate_test_partial(
    test_fn: Test,
    test_id: Optional[Union[int, str]] = None,
    display_name: Optional[str] = None,
    suite_test_id: Optional[int] = None,
    **params,
) -> TestPartial:
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

    if test_id is None:
        test_id = test_fn.meta.name if test_fn.meta.display_name is None else test_fn.meta.display_name

    return TestPartial(test_fn, actual_params, test_id, display_name, suite_test_id)


class Suite:
    """A test suite.

    A class representing a test suite that groups a collection of test cases together. The Suite class provides
    methods to add new tests, execute all tests, and save the suite to a Giskard instance.
    """

    id: Optional[int]
    project_key: Optional[str]
    tests: List[TestPartial]
    name: str
    default_params: Dict[str, Any]

    def __init__(self, name=None, default_params=None) -> None:
        """Create a new Test Suite instance with a given name.

        Parameters
        ----------
        name : Optional[str]
            The name of the test suite.
        default_params : dict, optional
            Any arguments passed will be applied to the tests in the suite, if runtime params with the same name are
            not set.
        """
        self.tests = list()
        self.name = name
        self.default_params = default_params if default_params else dict()
        self.id = None
        self.project_key = None

    def run(self, verbose: bool = True, **suite_run_args):
        """Execute all the tests that have been added to the test suite through the `add_test` method.

        Parameters
        ----------
        verbose : bool
            If set to `True`, the execution information for each test will be displayed. Defaults to `False`.
        **suite_run_args : Optional[dict]
            Any arguments passed here will be applied to all the tests in the suite whenever they match with the
            arguments defined for each test. If a test contains an argument that has already been defined, it will not
            get overridden. If any inputs on the test suite are missing, an error will be raised.

        Returns
        -------
        TestSuiteResult
            containing test execution information

        """
        execution_date = datetime.now()
        run_args = self.default_params.copy()
        run_args.update(suite_run_args)
        self.verify_required_params(run_args)

        results: List[SuiteResult] = list()

        for test_partial in self.tests:
            test_params = self.create_test_params(test_partial, run_args)

            try:
                result = test_partial.giskard_test(**test_params).execute()

                if isinstance(result, bool):
                    result = TestResult(passed=result)

                results.append(SuiteResult(test_partial.test_id, result, test_params, test_partial))
                if verbose:
                    print(
                        """Executed '{0}' with arguments {1}: {2}""".format(test_partial.test_id, test_params, result)
                    )
            except BaseException:  # noqa NOSONAR
                error = traceback.format_exc()
                logging.exception(f"An error happened during test execution for test: {test_partial.test_id}")
                results.append(
                    SuiteResult(
                        test_partial.test_id,
                        TestResult(
                            passed=False,
                            is_error=True,
                            messages=[TestMessage(type=TestMessageLevel.ERROR, text=error)],
                        ),
                        test_params,
                        test_partial,
                    )
                )

        passed = single_binary_result([r.result for r in results])

        logger.info(f"Executed test suite '{self.name or 'unnamed'}'")
        logger.info(f"result: {'success' if passed else 'failed'}")
        for test_name, r, params in results:
            logger.info(f"{test_name} ({params}): {format_test_result(r)}")

        return TestSuiteResult(self, run_args, passed, results, execution_date, datetime.now())

    def to_unittest(self, **suite_gen_args) -> List[TestPartial]:
        """Create a list of tests that can be easily passed for unittest execution using the `assert_` method

        Parameters
        ----------
        **suite_run_args : Optional[dict]
            Any arguments passed here will be applied to all the tests in the suite whenever they match with the
            arguments defined for each test. If a test contains an argument that has already been defined, it will not
            get overridden. If any inputs on the test suite are missing, an error will be raised.

        Returns
        -------
        List[TestPartial]
            containing the tests to execute in a unit test script
        """
        run_args = self.default_params.copy()
        run_args.update(suite_gen_args)

        unittests: List[TestPartial] = list()
        self.verify_required_params(run_args)

        for test_partial in self.tests:
            test_params = self.create_test_params(test_partial, run_args)
            unittest: TestPartial = test_partial.giskard_test(**test_params)
            params_str = ", ".join(
                f"{param}={getattr(value, 'name', None) or value}"  # Use attribute name if set
                for param, value in unittest.params.items()
            )
            fullname = f"{test_partial.test_id}({params_str})"
            # pass the test_id attribute to be used as unit test name
            setattr(unittest, "fullname", fullname)
            unittests.append(unittest)

        return unittests

    def verify_required_params(self, run_args: Dict[str, Any]):
        required_params = self.find_required_params()
        undefined_params = {k: v for k, v in required_params.items() if k not in run_args}

        if undefined_params:
            warning(f"Missing {len(undefined_params)} required parameters: {undefined_params}")

    @staticmethod
    def create_test_params(test_partial, kwargs) -> TestParams:
        if isinstance(test_partial.giskard_test, GiskardTestMethod):
            available_params = inspect.signature(test_partial.giskard_test.test_fn).parameters.items()
        else:
            available_params = inspect.signature(test_partial.giskard_test.__init__).parameters.items()

        test_params: TestParams = {}
        for pname, p in available_params:
            if pname in test_partial.provided_inputs:
                if isinstance(test_partial.provided_inputs[pname], SuiteInput):
                    test_params[pname] = kwargs[test_partial.provided_inputs[pname].name]
                else:
                    test_params[pname] = test_partial.provided_inputs[pname]
            elif pname in kwargs:
                test_params[pname] = kwargs[pname]
        return test_params

    def save(self, folder: str):
        folder_path = Path(folder)
        if folder_path.exists() and folder_path.is_file():
            raise ValueError(f"{folder_path} is a file, please provide a folder")

        folder_path.mkdir(parents=True, exist_ok=True)

        if self.name is None:
            self.name = "Unnamed test suite"

        saved_uuid_status: Dict[str, bool] = dict()

        json_content = self._to_json(folder_path, saved_uuid_status)

        with open(folder_path / "suite.json", "w") as f:
            json.dump(json_content, f)

        analytics.track("lib:test_suite:saved")

        return self

    def _to_json(self, folder: Path, saved_uuid_status: Dict[str, bool] = None):
        return {
            "name": self.name,
            "tests": [test._to_json(folder, saved_uuid_status) for test in self.tests],
            "function_inputs": [],
        }

    def add_test(
        self,
        test_fn: Test,
        test_id: Optional[Union[int, str]] = None,
        display_name: Optional[str] = None,
        **params,
    ) -> "Suite":
        """Add a test to the suite.

        Parameters
        ----------
        test_fn : Test
            A test method that will be executed or an instance of a GiskardTest class.
        test_id : Optional[Union[int, str]]
            A unique identifier used to track the test result.
            If None, the identifier will be generated based on the module and name of the test method.
            If the identifier already exists in the suite, a new unique identifier will be generated. (Default value = None)
        display_name : Optional[str]
            The name of the test to be displayed (Default value = None)
        **params :
            Default parameters to be passed to the test method.
            This parameter will be ignored if `test_fn` is an instance of GiskardTest.

        Returns
        -------
        Suite
            The current instance of the test suite to allow chained calls.

        """
        self.tests.append(generate_test_partial(test_fn, test_id, display_name, **params))

        return self

    def upgrade_test(
        self, test: GiskardTest, migrate_params_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> "Suite":
        """Upgrade a test with a new version, the test being upgraded are matched using display_name tests property.

        Parameters
        ----------
        test : GiskardTest
            The newest version of a test to be upgraded
        migrate_params_fn : Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]
            An optional callback used to migrate the old test params into the new params

        Returns
        -------
        Suite
            The current instance of the test suite to allow chained calls.

        """

        for test_to_upgrade in self.tests:
            if test_to_upgrade.giskard_test.display_name != test.display_name:
                continue

            test_to_upgrade.giskard_test = test
            if migrate_params_fn is not None:
                test_to_upgrade.provided_inputs = migrate_params_fn(test_to_upgrade.provided_inputs.copy())

        return self

    @singledispatchmethod
    def remove_test(self, arg):
        """Remove a test from the suite.

        Parameters
        ----------
        arg : int|str|GiskardTest
            If int: remove the test by index.
            If str: remove the test by name passed during the add_test method
            If GiskardTest: remove the test(s) by reference

        Returns
        -------
        Suite
            The current instance of the test suite to allow chained calls.

        """
        raise NotImplementedError("To remove a test from the suite please pass its index, its name or its reference")

    @remove_test.register
    def _remove_test_by_idx(self, idx: int):
        self.tests.pop(idx)
        return self

    @remove_test.register
    def _remove_test_by_name(self, test_name: str):
        self.tests = [test for test in self.tests if test.test_id != test_name]
        return self

    @remove_test.register
    def _remove_test_by_reference(self, giskard_test: GiskardTest):
        self.tests = [test for test in self.tests if test.giskard_test.meta.uuid != giskard_test.meta.uuid]
        return self

    def update_test_params(self, index: int, **params):
        """Update a test from the suite.

        Parameters
        ----------
        index : int
            The index of the test to be updated
        **params :
            The params to be added/updated to the current one

        Returns
        -------
        Suite
            The current instance of the test suite to allow chained calls.

        """
        test = self.tests[index]
        inputs = test.provided_inputs.copy()
        inputs.update(**params)
        self.tests[index] = generate_test_partial(test.giskard_test, test.test_id, **inputs)

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

        self.add_test(test_func, **suite_args)

    def _contains_test(self, test: TestFunctionMeta):
        return any(t.giskard_test == test for t in self.tests)

    @classmethod
    def load(cls, folder: str) -> "Suite":
        folder_path = Path(folder)

        with open(folder_path / "suite.json", "r") as f:
            suite_json = json.load(f)

        suite = Suite(name=suite_json.get("name", "Unnamed test suite"))

        for test_json in suite_json.get("tests", []):
            test_uuid = test_json.get("testUuid")
            test_folder = folder_path / test_uuid

            test = GiskardTest.load(test_folder, test_uuid, GiskardTest._load_meta_locally(test_folder, test_uuid))

            test_arguments = _parse_function_arguments(folder_path, test_json.get("functionInputs").values())
            suite.add_test(test(**test_arguments), suite_test_id=test_json.get("id"))

        return suite


def contains_tag(func: TestFunctionMeta, tag: str):
    return any([t for t in func.tags if t.upper() == tag.upper()])


def format_test_result(result: Union[bool, TestResult]) -> str:
    if isinstance(result, TestResult):
        return f"{{{'passed' if result.passed else 'failed'}, metric={result.metric}}}"
    else:
        return "passed" if result else "failed"


def _try_save_artifact(artifact, path: Path, saved_uuid_status: Dict[str, bool]) -> bool:
    artifact_id = serialize_parameter(artifact)

    if artifact_id not in saved_uuid_status:
        try:
            artifact_path = path / artifact_id
            artifact_path.mkdir(exist_ok=True)
            artifact.save(artifact_path)
            saved_uuid_status[artifact_id] = True
        except:  # noqa NOSONAR
            warning(f"Failed to save {str(artifact)} used in the test suite. The test suite will be partially saved.")
            saved_uuid_status[artifact_id] = False

    return saved_uuid_status[artifact_id]
