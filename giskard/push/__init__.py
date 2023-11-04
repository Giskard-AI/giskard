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
from typing import Optional

from abc import abstractmethod

from giskard.core.core import SupportedModelTypes
from giskard.ml_worker import websocket
from giskard.ml_worker.websocket import CallToActionKind, PushKind
from giskard.push.push_test_catalog.catalog import (
    one_sample_overconfidence_test,
    one_sample_underconfidence_test,
    test_diff_f1_push,
    test_diff_rmse_push,
    test_metamorphic_invariance_with_mad,
)
from giskard.push.utils import TransformationInfo
from giskard.slicing.slice import (
    ContainsWord,
    EqualTo,
    GreaterThan,
    LowerThan,
    Query,
    QueryBasedSliceFunction,
)
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

    @abstractmethod
    def to_ws(self):
        """
        Convert to gRPC protobuf format.
        """
        pass


class ExamplePush(Push):
    """
    Push class based on example data.

    Adds attributes:
        saved_example: Example dataset row
        training_label: Ground truth label
        training_label_proba: Probability of ground truth label

    Can convert to gRPC protobuf format.
    """

    saved_example = None
    training_label = None
    training_label_proba = None

    def to_ws(self):
        """
        Convert to gRPC protobuf format.
        """
        return websocket.Push(
            kind=self.pushkind,
            push_title=self.push_title,
            push_details=self.details,
        )


class FeaturePush(Push):
    """
    Push related to a specific feature.

    Adds attributes:
        feature: Feature name
        value: Feature value

    Can convert to gRPC protobuf format.
    """

    feature = None
    value = None

    def to_ws(self):
        """
        Convert to gRPC protobuf format.
        """
        return websocket.Push(
            kind=self.pushkind,
            key=self.feature,
            value=str(self.value),
            push_title=self.push_title,
            push_details=self.details,
        )


class OverconfidencePush(ExamplePush):
    """
    Recommand actions for overconfidence cases.

    Description:
        Tag examples that are incorrect but that were classified with a high probability as the wrong label.
        This may indicate that the model is overconfident on this example.
        This may be due to spurious correlation or a data leak

    Triggering event:
        When we switch examples, the example is incorrect and the example is classified as overconfident.
        We quantify this as the difference between the largest probability assigned to a label and the
        probability assigned to the correct label (this will be 0 if the model made the correct prediction).
        If this is larger than a threshold (typically determined automatically depending on
        the number of classes), then the prediction is considered overconfident.

    Call to action description:
        Create one-sample test : This adds a test that checks if the model is overconfident on this example to a test suite.
        Get similar examples : This filters the debugging session to show examples with overconfidence only.

    Requirements:
        Ground truth label
        Classification models only
    """

    def __init__(self, training_label, training_label_proba, dataset_row, predicted_label, rate):
        self._overconfidence()
        self.pushkind = PushKind.OVERCONFIDENCE

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row
        self.tests = [one_sample_overconfidence_test()]
        self.test_params = {"saved_example": self.saved_example}

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
                {
                    "action": "Generate a one-sample test to automatically check if this example is correctly predicted",
                    "explanation": "This enables you to make sure this specific example is correct for a new model",
                    "button": "Create one-sample test",
                    "cta": CallToActionKind.CREATE_TEST,
                },
                {
                    "action": "Inspect similar examples",
                    "explanation": "It will filter this debugging session to show similar examples with overconfidence",
                    "button": "Inspect similar examples",
                    "cta": CallToActionKind.OPEN_DEBUGGER_OVERCONFIDENCE,
                },
                # Disabled temporarily
                # {
                # "action": "Save this example for further inspection and testing",
                # "explanation": "This may help you identify spurious correlation and create one-sample tests based on these examples",
                # "button": "Save Example",
                #  "cta": CallToActionKind.SaveExample,
                # },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class BorderlinePush(ExamplePush):
    """
    Recommend actions for borderline/underconfidence cases.

    Description:
        Tag examples that are classified with very low confidence,
        indicating the model is unsure about the prediction.
        This may be due to inconsistent patterns or insufficient data.

    Triggering event:
        When we switch examples, the example is classified as underconfident.
        By default, we mark a prediction as underconfident when the second most
        probable prediction has a probability which is only less than 10%
        smaller than the predicted label

    Call to action description:
        Create one-sample test: This adds a test that checks if the model is underconfident on this example to a test suite.
        Get similar examples: This filters the debugging session to show examples with underconfidence only.

    Requirements:
        Classification models only
    """

    def __init__(self, training_label, training_label_proba, dataset_row, rate):
        self._borderline()
        self.pushkind = PushKind.BORDERLINE

        self.training_label_proba = training_label_proba
        self.training_label = training_label
        self.saved_example = dataset_row
        self.tests = [one_sample_underconfidence_test]
        self.test_params = {"saved_example": self.saved_example}

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
                {
                    "action": "Generate a one-sample to check for underconfidence",
                    "explanation": "This may help you ensure this specific example is not predicted with low "
                    "confidence for a new model",
                    "button": "Create one-sample test",
                    "cta": CallToActionKind.CREATE_TEST,
                },
                {
                    "action": "Inspect similar examples",
                    "explanation": "It will filter this debugging session to show similar examples with underconfidence",
                    "button": "Inspect similar examples",
                    "cta": CallToActionKind.OPEN_DEBUGGER_BORDERLINE,
                },
                # Disabled temporarily
                # {
                # "action": "Save this example for further inspection and testing",
                # "explanation": "This may help you identify inconsistent patterns and create one-sample tests based on these examples",
                # "button": "Save Example",
                # "cta": CallToActionKind.SaveExample,
                # },
            ],
        }
        self.push_title = res["push_title"]
        self.details = res["details"]


class ContributionPush(FeaturePush):
    """
    Recommend actions for feature that have high SHAP values.

    Description:
        Tag features that have a high SHAP value for this example.
        This may indicate that the model is relying heavily on this feature to make the prediction.

    Triggering event:
        When we switch examples and the most contributing shapley’s value
        is really high compared to the rest of the features.
        We mark a feature as high contributing by computing SHAP values
        for all features. Then we calculates z-scores to find any significant outliers.
        If the z-score is above a threshold (typically determined automatically
        depending on the number of features), then the feature is considered high contributing.


    Call to action description:
        Save Slice : This will save the slice in the catalog and enable you to create tests more efficiently.
        Add Test to a test suite : This will add a test to a test suite to check if this slice performs better or worse than the rest of the dataset.
        Get similar examples : This will filter this debugging session to show examples from this slice only.

    Requirements:
        Numerical and Categorical features only
    """

    slicing_function = None
    bounds = None
    model_type = None
    correct_prediction = None

    def __init__(
        self, value=None, feature=None, feature_type=None, bounds=None, model_type=None, correct_prediction=None
    ):
        self.pushkind = PushKind.CONTRIBUTION

        self.value = value
        self.bounds = bounds
        self.feature = feature
        self.feature_type = feature_type
        self.model_type = model_type
        self.correct_prediction = correct_prediction

        self._slicing_function()  # Needed for the message
        self._test_selection()
        self._set_title_and_details()

    def _set_title_and_details(self):
        """
        Generate title and details based on prediction.
        """
        if self.correct_prediction:
            if self.feature_type == "text":
                self.push_title = f'The word "{str(self.value)}" contributes a lot to the prediction'
            else:
                self.push_title = f"`{str(self.feature)}`=={str(self.value)} contributes a lot to the prediction"
            self.details = [
                {
                    "action": "Generate a Theil`s U test on similar examples",
                    "explanation": f"Theil`s U test will help you check the nominal association between {self.slicing_function.query} and the predicted label on the whole dataset",
                    "button": "Add Test to a test suite",
                    "cta": CallToActionKind.CREATE_TEST,
                },
                {
                    "action": "Inspect similar examples",
                    "explanation": "It will filter this debugging session to show similar examples",
                    "button": "Inspect similar examples",
                    "cta": CallToActionKind.CREATE_SLICE_OPEN_DEBUGGER,
                },
                {
                    "action": f"Save the {'quartile' if self.bounds is not None else 'slice'} {self.slicing_function.query} and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CREATE_SLICE,
                },
            ]
        else:
            if self.feature_type == "text":
                self.push_title = f'The word "{str(self.value)}" contributes a lot to the incorrect prediction'
            else:
                self.push_title = (
                    f"`{str(self.feature)}`=={str(self.value)} contributes a lot to the incorrect prediction"
                )
            self.details = [
                {
                    "action": "Generate a performance test on similar examples",
                    "explanation": "Performance (RMSE or F1) test will help you check if this slice performs better than the rest of the dataset",
                    "button": "Add Test to a test suite",
                    "cta": CallToActionKind.CREATE_TEST,
                },
                {
                    "action": "Inspect similar examples",
                    "explanation": "It will filter this debugging session to show similar examples",
                    "button": "Inspect similar examples",
                    "cta": CallToActionKind.CREATE_SLICE_OPEN_DEBUGGER,
                },
                {
                    "action": f"Save the {'quartile' if self.bounds is not None else 'slice'} {self.slicing_function.query} and continue debugging session",
                    "explanation": "Saving the slice will enable you to create tests more efficiently",
                    "button": "Save Slice",
                    "cta": CallToActionKind.CREATE_SLICE,
                },
            ]

    def _slicing_function(self):
        """
        Generate slicing function based on feature/value.
        """
        if self.feature_type == "text":
            clause = [ContainsWord(self.feature, self.value)]
        else:
            if self.bounds is not None:
                clause = [
                    GreaterThan(self.feature, self.bounds[0], True),
                    LowerThan(self.feature, self.bounds[1], True),
                ]
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
    Recommend actions for feature that perturb the prediction.

    Description:
        Tag features that when perturbed, change the prediction.
        This may indicate that the model is sensitive to this feature.

    Triggering event:
        When we switch examples and the prediction changes when we perturb a feature.
        We mark a feature as sensitive by applying supported perturbations to each feature in the dataset.
        For numerical columns, we add/subtract values based on mean absolute deviation.
        For text columns, we apply predefined text transformations.

    Call to action description:
        Add to test suite : This will add a test to a test suite to check if a
        perturbation on this feature changes the prediction above a threshold.

    Requirements:
        Need Ground truth label
        Numerical and Text features only
    """

    value_perturbed: Optional[list] = None
    transformation_functions: Optional[list] = None
    transformation_functions_params: Optional[list] = None
    details = [
        {
            "action": "Generate a metamorphic invariance test that slightly perturbs this feature",
            "explanation": "This will enable you to make sure the model is robust against similar small changes",
            "button": "Add to test suite",
            "cta": CallToActionKind.CREATE_TEST,
        },
    ]

    def __init__(self, value, feature, transformation_info: TransformationInfo):
        self.pushkind = PushKind.PERTURBATION
        self.feature = feature
        self.value = value
        self.value_perturbed = transformation_info.value_perturbed
        self.transformation_functions = transformation_info.transformation_functions
        self.transformation_functions_params = transformation_info.transformation_functions_params
        if self.transformation_functions_params:
            self.tests = [test_metamorphic_invariance_with_mad]
            self.test_params = self.transformation_functions_params[0]
            if self.value != 0:
                _relative_change = int(round((self.value_perturbed[0] - self.value) / self.value * 100.0))
            else:
                _relative_change = int(round((self.value_perturbed[0] * 100.0)))
            self.push_title = f"Changing `{self.feature}` by " f"{_relative_change}% " "makes the prediction change"
        else:
            self.tests = [test_metamorphic_invariance]
            self.test_params = {"transformation_function": self.transformation_functions[0]}
            self.push_title = f"""Perturbing `{self.feature}` ({self.transformation_functions[0].meta.display_name}) into "{self.value_perturbed[0]}" makes the prediction change"""
