from typing import Any

from giskard import TestResult, test
from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.ml_worker.generated import ml_worker_pb2
from giskard.ml_worker.generated.ml_worker_pb2 import CallToActionKind, PushKind
from giskard.models.base import BaseModel
from giskard.push.push_test_catalog.catalog import test_diff_f1_push, test_diff_rmse_push
from giskard.push.utils import TransformationInfo
from giskard.slicing.slice import EqualTo, GreaterThan, LowerThan, Query, QueryBasedSliceFunction
from giskard.testing.tests.calibration import test_overconfidence_rate, test_underconfidence_rate
from giskard.testing.tests.metamorphic import test_metamorphic_invariance
from giskard.testing.tests.statistic import test_theil_u


class Push:
    # list of numerical value or category
    push_title = None
    details = None
    tests = None
    pushkind = None


@test(name="If Underconfidence Decreases", tags=["custom"])
def if_underconfidence_rate_decrease(model: BaseModel, dataset: Dataset, rate: float):
    new_rate = test_underconfidence_rate(model, dataset).metric
    return TestResult(passed=new_rate < rate, metric=new_rate - rate)


@test(name="If Overconfidence Decreases", tags=["custom"])
def if_overconfidence_rate_decrease(model: BaseModel, dataset: Dataset, rate: float):
    new_rate = test_overconfidence_rate(model, dataset).metric
    return TestResult(passed=new_rate < rate, metric=new_rate - rate)


@test(name="Example Correctness", tags=["unit test", "custom"])
def correct_example(model: BaseModel, saved_example: Dataset, training_label: Any):
    prediction = model.predict(saved_example).prediction.values[0]
    return TestResult(passed=prediction == training_label, metric=prediction == training_label)


@test(name="Increase Probability", tags=["unit test", "custom"])
def increase_probability(model: BaseModel, saved_example: Dataset, training_label: Any, training_label_proba: Any):
    proba = model.predict(saved_example).all_predictions[training_label].values[0]
    return TestResult(passed=proba > training_label_proba, metric=proba - training_label_proba)


@test(name="One-Sample Overconfidence test", tags=["one-sample test", "custom"])
def one_sample_overconfidence_test(model: BaseModel, saved_example: Dataset):
    if model.is_classification:
        test_result = test_overconfidence_rate(model, saved_example).execute()
        return TestResult(passed=test_result.passed, metric=test_result.metric)


@test(name="One-Sample Underconfidence test", tags=["one-sample test", "custom"])
def one_sample_underconfidence_test(model: BaseModel, saved_example: Dataset):
    if model.is_classification:
        test_result = test_underconfidence_rate(model, saved_example).execute()
        return TestResult(passed=test_result.passed, metric=test_result.metric)


class ExamplePush(Push):
    saved_example = None
    training_label = None
    training_label_proba = None

    def to_grpc(self):
        return ml_worker_pb2.Push(
            kind=self.pushkind,
            push_title=self.push_title,
            push_details=self.details,
        )


class FeaturePush(Push):
    feature = None
    value = None

    def to_grpc(self):
        return ml_worker_pb2.Push(
            kind=self.pushkind,
            key=self.feature,
            value=str(self.value),
            push_title=self.push_title,
            push_details=self.details,
        )


class OverconfidencePush(ExamplePush):
    def __init__(self, training_label, training_label_proba, dataset_row, predicted_label, rate):
        self._overconfidence()
        self.pushkind = PushKind.Overconfidence

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row

        self.tests = [one_sample_overconfidence_test()]
        self.test_params = {"saved_example": dataset_row}
        # if_overconfidence_rate_decrease(rate=rate),
        #     correct_example(saved_example=dataset_row, training_label=training_label),
        #     increase_probability(
        #         saved_example=dataset_row, training_label=training_label, training_label_proba=training_label_proba
        #     ),
        self.predicted_label = predicted_label

    def _overconfidence(self):
        res = {
            "push_title": "This example is incorrect while having a high confidence.",
            "details": [
                # Disabled temporarily
                # {
                # "action": "Save this example for further inspection and testing",
                # "explanation": "This may help you identify spurious correlation and create one-sample tests based on these examples",
                # "button": "Save Example",
                #  "cta": CallToActionKind.SaveExample,
                # },
                {
                    "action": "Generate a one-sample test automatically to check if this example is correctly predicted",
                    "explanation": "This enables you to make sure this specific example is correct for a new model",
                    "button": "Create one-sample test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Filter this debugging session with similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.OpenDebuggerOverconfidence,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class BorderlinePush(ExamplePush):
    def __init__(self, training_label, training_label_proba, dataset_row, rate):
        self._borderline()
        self.pushkind = PushKind.Borderline

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row

        self.tests = [one_sample_underconfidence_test]
        self.test_params = {"saved_example": dataset_row}
        # [
        #     if_underconfidence_rate_decrease(rate=rate),
        #     correct_example(saved_example=dataset_row, training_label=training_label),
        #     increase_probability(
        #         saved_example=dataset_row, training_label=training_label, training_label_proba=training_label_proba
        #     ),
        # ]

    def _borderline(self):
        res = {
            "push_title": "This example was predicted with very low confidence",
            "details": [
                # Disabled temporarily
                # {
                # "action": "Save this example for further inspection and testing",
                # "explanation": "This may help you identify inconsistent patterns and create one-sample tests based on these examples",
                # "button": "Save Example",
                # "cta": CallToActionKind.SaveExample,
                # },
                {
                    "action": "Generate a one-sample test automatically the underconfidence",
                    "explanation": "This may help you ensure this example is not predicted with low confidence for a new model",
                    "button": "Create one-sample test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Filter this debugging session with similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.OpenDebuggerBorderline,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class ContributionPush(FeaturePush):
    slicing_function = None
    bounds = None
    model_type = None
    correct_prediction = None

    def __init__(self, value=None, feature=None, bounds=None, model_type=None, correct_prediction=None):
        self.pushkind = PushKind.Contribution

        self.value = value
        self.bounds = bounds
        self.feature = feature
        self.model_type = model_type
        self.correct_prediction = correct_prediction

        self._slicing_function()
        self._set_title_and_details()
        self._test_selection()

    def _set_title_and_details(self):
        if self.correct_prediction:
            self.push_title = f"{str(self.feature)}=={str(self.value)} contributes a lot to the prediction"
            self.details = [
                {
                    "action": "Save slice and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CreateSlice,
                },
                {
                    "action": "Generate a test to check if this correlation holds with the whole dataset",
                    "explanation": "Correlations may be spurious, double check if it has a business sense",
                    "button": "Create Test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Filter this debugging session with similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.CreateSliceOpenDebugger,
                },
            ]
        else:
            self.push_title = f"{str(self.feature)}=={str(self.value)} is responsible for the incorrect prediction"
            self.details = [
                {
                    "action": "Save slice and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CreateSlice,
                },
                {
                    "action": "Generate a test to check if this correlation holds with the whole dataset",
                    "explanation": "Correlations may be spurious, double check if it has a business sense",
                    "button": "Create Test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Filter this debugging session with similar examples",
                    "explanation": "Debugging similar examples may help you find common spurious patterns",
                    "button": "Open Debugger",
                    "cta": CallToActionKind.CreateSliceOpenDebugger,
                },
            ]

    def _slicing_function(self):
        if self.bounds is not None:
            clause = [GreaterThan(self.feature, self.bounds[0], True), LowerThan(self.feature, self.bounds[1], True)]
        else:
            clause = [EqualTo(self.feature, self.value)]
        slicing_func = QueryBasedSliceFunction(Query(clause))
        self.slicing_function = slicing_func
        self.test_params = {"slicing_function": slicing_func}

    def _test_selection(self):
        if not self.correct_prediction:
            if self.model_type == SupportedModelTypes.REGRESSION:
                self.tests = [test_diff_rmse_push]
            elif self.model_type == SupportedModelTypes.CLASSIFICATION:
                self.tests = [test_diff_f1_push]
        elif self.correct_prediction:
            self.tests = [test_theil_u]


class PerturbationPush(FeaturePush):
    text_perturbed: list = None
    transformation_function: list = None
    details = [
        {
            "action": "Generate a robustness test that slightly perturb this feature",
            "explanation": "This will enable you to make sure the model is robust against similar small changes",
            "button": "Create test",
            "cta": CallToActionKind.CreateTest,
        },
    ]

    def __init__(self, value, feature, transformation_info: TransformationInfo):
        self.pushkind = PushKind.Perturbation
        self.feature = feature
        self.value = value
        self.text_perturbed = transformation_info.text_perturbed
        self.transformation_functions = transformation_info.transformation_functions
        self.tests = [test_metamorphic_invariance]
        self.test_params = {"transformation_function": self.transformation_functions}
        self.push_title = f"A small variation of {str(feature)}=={str(value)} makes the prediction change"
