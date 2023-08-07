from enum import Enum

from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.generated import ml_worker_pb2
from giskard.ml_worker.generated.ml_worker_pb2 import CallToActionKind, PushKind
from giskard.models.base import BaseModel
from giskard.push.push_test_catalog.catalog import test_diff_f1_push, test_diff_rmse_push
from giskard.slicing.slice import EqualTo, GreaterThan, LowerThan, Query, QueryBasedSliceFunction
from giskard.testing.tests.metamorphic import test_metamorphic_invariance


class SupportedPerturbationType(Enum):
    NUMERIC = "numeric"
    TEXT = "text"


class Push:
    # list of numerical value or category
    push_title = None
    details = None
    tests = None
    pushkind = None


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

    def _increase_proba(self):
        from giskard import TestResult, test

        @test(name="Increase Probability", tags=["unit test", "custom"])
        def increase_probability(model: BaseModel):
            proba = model.predict(self.saved_example).all_predictions[self.training_label].values[0]
            return TestResult(passed=proba > self.training_label_proba, metric=proba - self.training_label_proba)

        return increase_probability

    def _check_if_correct(self):
        from giskard import TestResult, test

        @test(name="Example Correctness", tags=["unit test", "custom"])
        def correct_example(model: BaseModel):
            prediction = model.predict(self.saved_example).prediction.values[0]
            return TestResult(passed=prediction == self.training_label, metric=prediction == self.training_label)

        return correct_example


class OverconfidencePush(ExamplePush):
    def __init__(self, training_label, training_label_proba, dataset_row, predicted_label):
        self._overconfidence()
        self.pushkind = PushKind.Overconfidence

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row

        self.tests = [self._increase_proba()]  # TODO: Add Overconfidence rate test
        self.unit_tests = [self._increase_proba(), self._check_if_correct()]
        # To complete debugger filter
        self.predicted_label = predicted_label

    def _overconfidence(self):
        res = {
            "push_title": "This example is incorrect while having a high confidence.",
            "details": [
                # Disabled temporarily
                # {
                #    "action": "Save this example for further inspection and testing",
                #    "explanation": "This may help you identify spurious correlation and create unit test based on "
                #    "these examples",
                #    "button": "Save Example",
                #    "cta": CallToActionKind.SaveExample,
                # },
                {
                    "action": "Generate unit tests to check if this example is correctly predicted",
                    "explanation": "This enables you to make sure this specific example is correct for a new model",
                    "button": "Create unit tests",
                    "cta": CallToActionKind.CreateUnitTest,
                },
                {
                    "action": "Generate a test to check if the rate of <br>overconfidence</br> rows is decreasing",
                    "explanation": "This may help you ensure that the overconfidence rate is at an acceptable level",
                    "button": "Create test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Filter this debugger session with similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.OpenDebuggerOverconfidence,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class BorderlinePush(ExamplePush):
    def __init__(self, max_proba, second_proba, training_label, training_label_proba, dataset_row):
        self._borderline()
        self.pushkind = PushKind.Borderline
        self.max_proba = max_proba
        self.second_proba = second_proba

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row

        self.tests = [self._increase_proba()]  # TODO: Add Underconfidence rate test
        self.unit_tests = [self._increase_proba(), self._check_if_correct()]

    def _borderline(self):
        res = {
            "push_title": "This example was predicted with very low confidence",
            "details": [
                # Disabled temporarily
                # {
                #    "action": "Save this example for further inspection and testing",
                #    "explanation": "This may help you identify inconsistent patterns and create a unit test based "
                #                   "on these examples",
                #    "button": "Save Example",
                #    "cta": CallToActionKind.SaveExample,
                # },
                {
                    "action": "Generate tests specific to this example",
                    "explanation": "This may help you ensure that this example is not predicted with low confidence "
                    "for a new model",
                    "button": "Create test",
                    "cta": CallToActionKind.CreateUnitTest,
                },
                {
                    "action": "Generate a test to check if the rate of <br>underconfidence</br> rows is decreasing",
                    "explanation": "This may help you ensure that the underconfidence rate is at an acceptable level",
                    "button": "Create test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Open the debugger session on similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.OpenDebuggerBorderline,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


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


class ContributionPush(FeaturePush):
    slicing_function = None
    bounds = None
    model_type = None
    correct_prediction = None

    def __init__(self, value=None, feature=None, bounds=None, model_type=None, correct_prediction=None):
        self.pushkind = PushKind.Contribution
        # FeaturePush attributes initialisation
        self.value = value
        self.bounds = bounds
        # ContributionPush attributes initialisation
        self.feature = feature
        self.model_type = model_type
        self.correct_prediction = correct_prediction
        # Slice creation
        self._slicing_function()
        # Push text creation

    def _contribution_incorrect(self, feature, value):
        res = {
            "push_title": f"{str(feature)}=={str(value)} is responsible for the incorrect prediction",
            "details": [
                {
                    "action": "Filter this debugger session with similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.CreateSliceOpenDebugger,
                },
                {
                    "action": "Generate a performance difference test",
                    "explanation": "This may help ensure this spurious pattern is not common to the whole dataset",
                    "button": "Create test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Save slice and continue debugging session",
                    "explanation": "Saving the slice will enable you to use it later",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CreateSlice,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]
        return res

    def _contribution_correct(self, feature, value):  # ON HOLD
        res = {
            "push_title": f"{str(feature)}=={str(value)} contributes a lot to the prediction",
            "details": [
                {
                    "action": "Open the debugger session on similar examples",
                    "explanation": "Debugging similar examples may help you find common patterns",
                    "button": "Open debugger",
                    "cta": CallToActionKind.CreateSliceOpenDebugger,
                },
                {
                    "action": "Generate a test to check if this correlation holds with the whole dataset",
                    "explanation": "Correlations may be spurious, double check if it has a business sense",
                    "button": "Create test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "Save slice and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CreateSlice,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]
        return res

    def _slicing_function(self):
        if isinstance(self.bounds, list):
            clause = [GreaterThan(self.feature, self.bounds[0], True), LowerThan(self.feature, self.bounds[1], True)]
        else:
            clause = [EqualTo(self.feature, self.bounds)]
        slicing_func = QueryBasedSliceFunction(Query(clause))
        self.slicing_function = slicing_func

    def _test_selection(self, slicing_fn: QueryBasedSliceFunction, correct_prediction):
        if not correct_prediction:
            if self.model_type == SupportedModelTypes.REGRESSION:
                self.tests = [test_diff_rmse_push(slicing_function=slicing_fn)]
            elif self.model_type == SupportedModelTypes.CLASSIFICATION:
                self.tests = [test_diff_f1_push(slicing_function=slicing_fn)]
        # TODO
        # else:
        #     if self.model_type == SupportedModelTypes.REGRESSION:
        #         self.tests = [test_diff_rmse_push(slicing_function=slicing_fn)]
        #     elif self.model_type == SupportedModelTypes.CLASSIFICATION:
        #         self.tests = [test_f1(slicing_function=slicing_fn, threshold=0.5)]


class PerturbationPush(FeaturePush):
    text_perturbed: list = None
    transformation_function: list = None

    def __init__(self, value=None, feature=None, text_perturbed=None, transformation_function=None):
        self.pushkind = PushKind.Perturbation
        # FeaturePush attributes
        self.feature = feature
        self.value = value
        # PerturbationPush attributes
        self.text_perturbed = text_perturbed
        self.transformation_function = transformation_function
        self.tests = [test_metamorphic_invariance(transformation_function=self.transformation_function)]
        # Push text creation
        self._perturbation(feature, value)

    def _perturbation(self, feature, value):
        res = {
            "push_title": f"A small variation of {str(feature)}=={str(value)} makes the prediction change",
            "details": [
                {
                    "action": "Generate a robustness test that slightly perturb this feature",
                    "explanation": "This will enable you to make sure the model is invariant against small similar "
                    "changes",
                    "button": "Create test",
                    "cta": CallToActionKind.CreateTest,
                },
            ],
        }

        self.push_title = res["push_title"]
        self.details = res["details"]
        return res
