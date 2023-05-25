from enum import Enum

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.ml_worker.generated import ml_worker_pb2
from giskard.ml_worker.testing.test_result import TestResult
from giskard.models.base import BaseModel
from giskard.slicing.slice import GreaterThan, LowerThan, EqualTo, Query, QueryBasedSliceFunction
from giskard.testing.tests.metamorphic import test_metamorphic_invariance
from giskard.testing.tests.performance import test_f1, test_rmse
from ml_worker_pb2 import CallToActionKind, PushKind


class SupportedPerturbationType(Enum):
    NUMERIC = "numeric"
    TEXT = "text"


class Push:
    # list of numerical value or category
    push_title = None
    details = None
    test = None
    pushkind = None


class ExamplePush(Push):
    dataset_row = None
    training_label = None
    training_label_proba = None

    def to_grpc(self):
        return ml_worker_pb2.Push(
            kind=self.pushkind,
            push_title=self.push_title,
            push_details=self.details,
        )

    def _increase_proba(self):
        def _custom_unit_test(model: BaseModel, dataset: Dataset, threshold: float = 1) -> TestResult:
            proba = model.predict(self.dataset_row).all_predictions[self.training_label].values
            return TestResult(passed=proba > self.training_label_proba, metric=proba - self.training_label_proba)

        return _custom_unit_test

    def _check_if_correct(self):
        def _custom_unit_test(model: BaseModel, dataset: Dataset, threshold: float = 1) -> TestResult:
            prediction = model.predict(self.dataset_row).prediction.values
            return TestResult(passed=prediction == self.training_label, metric=prediction == self.training_label)

        return _custom_unit_test


class OverconfidencePush(ExamplePush):

    def __init__(self, training_label, training_label_proba, dataset_row, predicted_label):
        self._overconfidence()
        self.pushkind = PushKind.Overconfidence

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row

        self.tests = [self._increase_proba(), self._check_if_correct]
        # To complete debugger filter
        self.predicted_label = predicted_label

    def _overconfidence(self):
        res = {"push_title": "This example is incorrect while having a high confidence.",
               "details":
                   [{
                       "action": "Save this example for further inspection and testing",
                       "explanation": "This may help you identify spurious correlation and create unit test based on "
                                      "these examples",
                       "button": "Save Example",
                       "cta": CallToActionKind.SaveExample
                   },
                       {
                           "action": "Generate a unit test to check if this example has the right label",
                           "explanation": "This enables you to make sure this specific example has the right label "
                                          "with enough confidence",
                           "button": "Create test",
                           "cta": CallToActionKind.AddTestToCatalog
                       },
                       {
                           "action": "Open the debugger session on similar examples",
                           "explanation": "Debugging similar examples may help you find common patterns",
                           "button": "Open debugger",
                           "cta": CallToActionKind.OpenDebuggerOverconfidence
                       }
                   ]
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

        self.tests = [self._increase_proba(), self._check_if_correct]

    def _borderline(self):
        res = {"push_title": "This example was predicted with very low confidence",
               "details":
                   [{
                       "action": "Save this example for further inspection and testing",
                       "explanation": "This may help you identify inconsistent patterns and create a unit test based "
                                      "on these examples",
                       "button": "Save Example",
                       "cta": CallToActionKind.SaveExample
                   },
                       {
                           "action": "Generate an inconsistency test",
                           "explanation": "This may help you ensure this inconsistent pattern is not common to the "
                                          "whole dataset",
                           "button": "Create test",
                           "cta": CallToActionKind.AddTestToCatalog
                       },
                       {
                           "action": "Open the debugger session on similar examples",
                           "explanation": "Debugging similar examples may help you find common patterns",
                           "button": "Open debugger",
                           "cta": CallToActionKind.OpenDebuggerBorderline
                       }

                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]


class FeaturePush(Push):
    key = None
    value = None

    def to_grpc(self):
        return ml_worker_pb2.Push(
            kind=self.pushkind,
            key=self.key,
            value=str(self.value),
            push_title=self.push_title,
            push_details=self.details,
        )


class ContributionPush(FeaturePush):
    slicing_function = None
    bounds = None
    model_type = None
    correct_prediction = None
    test = None

    def __init__(self, value=None, feature=None, bounds=None, model_type=None, correct_prediction=None):
        self.pushkind = PushKind.Contribution
        # FeaturePush attributes initialisation
        self.value = value
        self.bounds = bounds
        # ContributionPush attributes initialisation
        self.feature = feature
        self.model_type = model_type
        # Push text creation
        if correct_prediction:
            self._contribution_correct(feature, value)
        elif not correct_prediction:
            self._contribution_incorrect(feature, value)
        else:
            pass
        # Test and Slice creation
        self._slicing_function()
        self._test_selection()

    def _contribution_incorrect(self, feature, value):
        res = {"push_title": f"{str(feature)}=={str(value)} is responsible for the incorrect prediction",
               "details":
                   [{
                       "action": "Open the debugger session on similar examples",
                       "explanation": "Debugging similar examples may help you find common spurious patterns",
                       "button": "Open debugger",
                       "cta": CallToActionKind.CreateSliceOpenDebugger
                   },
                       {
                           "action": "Generate a new performance difference test",
                           "explanation": "This may help ensure this spurious pattern is not common to the whole "
                                          "dataset",
                           "button": "Create test",
                           "cta": CallToActionKind.CreateTest
                       },
                       {
                           "action": "Save slice and continue debugging session",
                           "explanation": "Saving the slice will enable you to create tests more efficiently",
                           "button": "Save Slice",
                           "cta": CallToActionKind.CreateSlice
                       }
                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]
        return res

    def _contribution_correct(self, feature, value):
        res = {"push_title": f"{str(feature)}=={str(value)} contributes a lot to the prediction",
               "details":
                   [{
                       "action": "Open the debugger session on similar examples",
                       "explanation": "Debugging similar examples may help you find common patterns",
                       "button": "Open debugger",
                       "cta": CallToActionKind.CreateSliceOpenDebugger
                   },
                       {
                           "action": "Generate a test to check if this correlation holds with the whole dataset",
                           "explanation": "Correlations may be spurious, double check if it has a business sense",
                           "button": "Create test",
                           "cta": CallToActionKind.CreateTest
                       },
                       {
                           "action": "Save slice and continue debugging session",
                           "explanation": "Saving the slice will enable you to create tests more efficiently",
                           "button": "Save Slice",
                           "cta": CallToActionKind.CreateSlice
                       }
                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]
        return res

    def _slicing_function(self):
        if isinstance(self.bounds, list):
            clause = [GreaterThan(self.key, self.bounds[0], True), LowerThan(self.key, self.bounds[1], True)]
        else:
            clause = [EqualTo(self.key, self.bounds, True)]
        slicing_func = QueryBasedSliceFunction(Query(clause))
        self.slicing_function = slicing_func

    def _test_selection(self):
        if self.model_type == SupportedModelTypes.REGRESSION:
            self.test = test_f1
        elif self.model_type == SupportedModelTypes.CLASSIFICATION:
            self.test = test_rmse


class PerturbationPush(FeaturePush):
    text_perturbed: list = None
    transformation_function: list = None
    test = test_metamorphic_invariance

    def __init__(self, value=None, feature=None, text_perturbed=None, transformation_function=None):
        self.pushkind = PushKind.Perturbation
        # FeaturePush attributes
        self.key = feature
        self.value = value
        # PerturbationPush attributes
        self.text_perturbed = text_perturbed
        self.transformation_function = transformation_function
        # Push text creation
        self._perturbation(feature, value)

    def _perturbation(self, feature, value):
        res = {"push_title": f"A small variation of {str(feature)}=={str(value)} makes the prediction change",
               "details":
                   [{
                       "action": "Generate a robustness test that slightly perturb this feature",
                       "explanation": "This will enable you to make sure the model is robust against small similar "
                                      "changes",
                       "button": "Create test",
                       "cta": CallToActionKind.RobustnessTest
                   },
                       {
                           "action": "Save the perturbation that made the model change and continue debugging session",
                           "explanation": "Saving this perturbation will enable you to create tests more efficiently",
                           "button": "Save Perturbation",
                           "cta": CallToActionKind.SavePerturbation
                       }
                   ]
               }

        self.push_title = res["push_title"]
        self.details = res["details"]
        return res
