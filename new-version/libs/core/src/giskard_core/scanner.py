from typing import Any, Callable, Dict, List, Tuple, Type, Union

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from giskard_core.dataset import Dataset
from giskard_core.model import Model


class Status(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


RuntimeTestArguments = Dict[str, Union[Model, Dataset]]


@dataclass(frozen=True)
class TestExecution:
    test: Type["Test"]
    init_parameters: Dict[str, Any]
    runtime_arguments: RuntimeTestArguments
    result: Any
    passed: Status


class Test(ABC):
    name: str  # human readable id

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super().__init__()
        self._init_params = kwargs

    # display_name: str

    @abstractmethod
    def run(self, **kwargs: RuntimeTestArguments) -> Tuple[bool, Any]:
        raise NotImplementedError

    def __call__(self, **kwargs: RuntimeTestArguments):
        try:
            passed, meta = self.run(**kwargs)
            passed = Status.PASSED if passed else Status.FAILED
        except Exception as e:
            passed = Status.ERROR
            meta = {"exception": str(e)}

        return TestExecution(
            test=self.__class__,
            init_parameters=self._init_params,
            runtime_arguments=kwargs,
            result=meta,
            passed=passed,
        )


class ActualTest(Test):

    def run(self, dataset: Dataset, model: Model) -> Tuple[bool, Any]:
        return any(model(dataset)), None


# def test(threshold, ...):

#     def local_test(model, dataset):
#         # do stuff
#         return False

#     return local_test


# inst: TestExecution = TestExecution()
# inst.test(**inst.init_parameters).run(**inst.runtime_arguments)

# inst.test(**inst.init_parameters).run(
#     model=model2, dataset=newdata
# )
# MODEL DATASET

# -> DATASET[SEX = H]
# -> TEST()(runtimeargs DATASET[SEX = H])

# SCANNER -> SUITE
# SUITE.RUN()


TestType = Callable[[Model, Dataset], Tuple[bool, Any]]


class BasicTest(Test):
    def __init__(self, test_fn: TestType) -> None:
        super().__init__(**kwargs)
        self.test_fn = test_fn

    def run(self, dataset: Dataset, model: Model) -> Tuple[bool, Any]:
        return self.test_fn(model, dataset)


# class BasicSlicingTest(Test):
#     def __init__(self, test_fn: TestType) -> None:
#         super().__init__(**kwargs)
#         self.test_fn = test_fn

#     def run(self, dataset: Dataset, model: Model) -> Tuple[bool, Any]:
#         return self.test_fn(model, dataset)
class WrapperTest(Test):

    def __init__
    # def


class MetricTest(Test):
    def __init__(
        self, metric: Callable, threshold: float, lower_is_better: bool = False
    ) -> None:
        super().__init__(**kwargs)
        self.metric = metric
        self.threshold = threshold
        self.lower_is_better = lower_is_better

    def run(self, dataset: Dataset, model: Model):
        return self.metric(model.predict(dataset)) <= self.threshold


# MetricTest(AUC, O.7, False).run()

# Test(**parameters_const).run(**runtime_parameters)


class Detector(ABC):

    @abstractmethod
    def detect(self, model: Model, dataset: Dataset) -> List[TestExecution]:
        raise NotImplementedError

    # @abstractmethod
    # def generate_datasets(self) -> List[Dataset]:
    #     raise NotImplementedError

    # @abstractmethod
    # def get_tests(self) -> List[Test]:
    #     raise NotImplementedError

    # def detect(self) -> List[Tuple[Test, Params]]:
    #     datasets = self.generate_datasets()
    #     tests = self.get_tests()
    #     # TODO(Bazire): test task
    #     # Test(params)(model, dataset)
    #     raise NotImplementedError
    #     # return [TestTask() for t in self.get_tests() for d in ]


class Scanner(ABC):

    @classmethod
    @abstractmethod
    def get_detectors(self) -> List[Detector]:
        raise NotImplementedError

    def scan(self, model: Model, dataset: Dataset):
        detectors = self.get_detectors()

        all_issues = []
        for detector in detectors:
            executions = detector.detect(model, dataset)

            all_issues.extend(executions)
            # configured_tests, generated_datasets = detector.detect(model, dataset)
            # run_list.extend(
            #     [configured_tests.prepare(model, d) for d in generated_datasets]
            # )

        return all_issues

    # @classmethod
    # def scan(cls, dataset: Dataset, model: Model):
    #     detectors = cls.get_detectors()

    #     pass


class TabularScanne(Scanner):

    def get_detectors(self) -> List[Detector]:
        raise NotImplementedError
