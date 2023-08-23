"""
This module defines various push classes used for model debugging.

The main classes are:

- Push: Base push class  
- ExamplePush: Push based on example data
- OverconfidencePush: Push for overconfidence cases
- BorderlinePush: Push for borderline/underconfidence cases
- ContributionPush: Push for high contribution features
- PerturbationPush: Push for perturbation analysis

ExamplePush and its subclasses allow saving examples and generating
one-sample tests. ContributionPush and PerturbationPush allow generating
statistical tests and slicing functions.

The push classes allow converting to gRPC protobuf format via the to_grpc() method.
"""

from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.generated import ml_worker_pb2
from giskard.ml_worker.generated.ml_worker_pb2 import CallToActionKind, PushKind
from giskard.push.push_test_catalog.catalog import (
    one_sample_overconfidence_test,
    one_sample_underconfidence_test,
    test_diff_f1_push,
    test_diff_rmse_push,
    test_metamorphic_invariance_with_mad,
)
from giskard.push.utils import TransformationInfo
from giskard.slicing.slice import EqualTo, GreaterThan, LowerThan, Query, QueryBasedSliceFunction
from giskard.testing.tests.metamorphic import test_metamorphic_invariance
from giskard.testing.tests.statistic import test_theil_u


class Push:
    """
    Base push class.

    Attributes:
        push_title: Title of the push
        details: List of details/actions for the push
        tests: List of tests to generate
        pushkind: Enum of push kind
    """

    push_title = None
    details = None
    tests = None
    pushkind = None


class ExamplePush(Push):
    """
    Push class based on example data.

    Adds attributes:
        saved_example: Example dataset row
        training_label: Ground truth label
        training_label_proba: Probability of ground truth label
    """

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
        """
        Convert to gRPC protobuf format.
        """
        return ml_worker_pb2.Push(
            kind=self.pushkind,
            key=self.feature,
            value=str(self.value),
            push_title=self.push_title,
            push_details=self.details,
        )


class OverconfidencePush(ExamplePush):
    """
    Push for overconfidence cases.

    Attributes:
        training_label: Ground truth label
        training_label_proba: Probability of ground truth label
        saved_example: Example dataset row
        predicted_label: Model predicted label
        rate: Overconfidence rate

    Generates title, details, tests for overconfidence push.
    """

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
        """
        Generate overconfidence push title and details.
        """
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
                    "action": "Generate a one-sample test to automatically check if this example is correctly predicted",
                    "explanation": "This enables you to make sure this specific example is correct for a new model",
                    "button": "Create one-sample test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "See similar examples",
                    "explanation": "It will filter this debugging session to show examples with overconfidence only",
                    "button": "Get similar examples",
                    "cta": CallToActionKind.OpenDebuggerOverconfidence,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class BorderlinePush(ExamplePush):
    """
    Push for borderline/underconfidence cases.

    Attributes:
        training_label: Ground truth label
        training_label_proba: Probability of ground truth label
        saved_example: Example dataset row
        rate: Underconfidence rate

    Generates title, details, tests for borderline push.
    """

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
        """
        Generate borderline push title and details.
        """
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
                    "action": "Generate a one-sample to automatically test the underconfidence",
                    "explanation": "This may help you ensure this example is not predicted with low confidence for a new model",
                    "button": "Create one-sample test",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "See similar examples",
                    "explanation": "It will filter this debugging session to show examples with underconfidence only",
                    "button": "Get similar examples",
                    "cta": CallToActionKind.OpenDebuggerBorderline,
                },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class ContributionPush(FeaturePush):
    """
    Push for high contribution features.

    Attributes:
        feature: Feature name
        value: Feature value
        bounds: Value bounds if feature is numerical
        model_type: Model type (classification/regression)
        correct_prediction: If contribution causes correct/incorrect prediction

    Generates title, details, tests, slicing function based on attributes.
    """

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
        """
        Generate title and details based on prediction.
        """
        if self.correct_prediction:
            self.push_title = f"{str(self.feature)}=={str(self.value)} contributes a lot to the prediction"
            self.details = [
                {
                    "action": f"Save the slice {self.slicing_function.query} and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CreateSlice,
                },
                {
                    "action": "Automatically generate a test ",
                    "explanation": "Theil`s U test will help you check the correlation on the whole dataset, check our documentation for more info",
                    "button": "Add Test to a test suite",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "See similar examples",
                    "explanation": "It will filter this debugging session to show examples from this slice only",
                    "button": "Get similar examples",
                    "cta": CallToActionKind.CreateSliceOpenDebugger,
                },
            ]
        else:
            self.push_title = f"{str(self.feature)}=={str(self.value)} contributes a lot to the incorrect prediction"
            self.details = [
                {
                    "action": f"Save the slice {self.slicing_function.query} and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CreateSlice,
                },
                {
                    "action": "Automatically generate a test",
                    "explanation": "Performance (RMSE or F1) test will help you check if this slice performs better than the rest of the dataset, check our documentation for more info",
                    "button": "Add Test to a test suite",
                    "cta": CallToActionKind.CreateTest,
                },
                {
                    "action": "See similar examples",
                    "explanation": "It will filter this debugging session to show examples from this slice only",
                    "button": "Get similar examples",
                    "cta": CallToActionKind.CreateSliceOpenDebugger,
                },
            ]

    def _slicing_function(self):
        """
        Generate slicing function based on feature/value.
        """
        if self.bounds is not None:
            clause = [GreaterThan(self.feature, self.bounds[0], True), LowerThan(self.feature, self.bounds[1], True)]
        else:
            clause = [EqualTo(self.feature, self.value)]
        slicing_func = QueryBasedSliceFunction(Query(clause))
        self.slicing_function = slicing_func
        self.test_params = {"slicing_function": slicing_func}

    def _test_selection(self):
        """
        Select statistical test based on prediction type.
        """
        if not self.correct_prediction:
            if self.model_type == SupportedModelTypes.REGRESSION:
                self.tests = [test_diff_rmse_push]
            elif self.model_type == SupportedModelTypes.CLASSIFICATION:
                self.tests = [test_diff_f1_push]
        elif self.correct_prediction:
            self.tests = [test_theil_u]


class PerturbationPush(FeaturePush):
    """
    Push for perturbation analysis.

    Attributes:
        feature: Feature name
        value: Original feature value
        value_perturbed: Perturbed feature values
        transformation_functions: Perturbation functions
        transformation_functions_params: Function parameters
        details: Default details

    Generates title, tests based on perturbation.
    """

    value_perturbed: list = None
    transformation_functions: list = None
    transformation_functions_params: list = None
    details = [
        {
            "action": "Generate a metamorphic invariance test that slightly perturbs this feature",
            "explanation": "This will enable you to make sure the model is robust against similar small changes",
            "button": "Add to test suite",
            "cta": CallToActionKind.CreateTest,
        },
    ]

    def __init__(self, value, feature, transformation_info: TransformationInfo):
        self.pushkind = PushKind.Perturbation
        self.feature = feature
        self.value = value
        self.value_perturbed = transformation_info.value_perturbed
        self.transformation_functions = transformation_info.transformation_functions
        self.transformation_functions_params = transformation_info.transformation_functions_params
        if self.transformation_functions_params:
            self.tests = [test_metamorphic_invariance_with_mad]
            self.test_params = self.transformation_functions_params[0]
            self.push_title = (
                f"Adding {round(self.value_perturbed[0] - self.value,2)} to {self.feature} makes the prediction change"
            )
        else:
            self.tests = [test_metamorphic_invariance]
            self.test_params = {"transformation_function": self.transformation_functions[0]}
            self.push_title = f"Perturbing {self.feature} into {self.value_perturbed[0]} makes the prediction change"
