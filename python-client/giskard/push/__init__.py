from giskard.ml_worker.generated import ml_worker_pb2
from giskard.slicing.slice import GreaterThan, LowerThan, EqualTo, Query, QueryBasedSliceFunction
from enum import Enum
from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.testing.tests.performance import test_f1, test_rmse


class SupportedPerturbationType(Enum):
    NUMERIC = "numeric"
    TEXT = "text"


class Push:
    # list of numerical value or category
    push_title = None
    details = None
    test = None

    def to_grpc(self):
        return ml_worker_pb2.Push(
            key=self.key,
            value=str(self.value),
            push_title=self.push_title,
            push_details=self.details,
        )


class ExamplePush(Push):
    pass


class OverconfidencePush(ExamplePush):
    def __init__(self):
        self._overconfidence()
        # self.test = test_overconfidence @TODO: add this test

    def _overconfidence(self):
        res = {"push_title": "This example is incorrect while having a high confidence.",
               "details":
                   [{
                       "action": "Save this example for further inspection and testing",
                       "explanation": "This may help you identify spurious correlation and create unit test based on "
                                      "these examples",
                       "button": "Save Example"
                   },
                       {
                           "action": "Generate an overconfidence test",
                           "explanation": "This may help you ensure this overconfidence pattern is not common to the "
                                          "whole dataset",
                           "button": "Create test"
                       }
                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]


class BorderlinePush(ExamplePush):
    def __init__(self):
        self._borderline()
        # self.test = test_borderline @TODO: add this test

    def _borderline(self):
        res = {"push_title": "This example was predicted with very low confidence",
               "details":
                   [{
                       "action": "Save this example for further inspection and testing",
                       "explanation": "This may help you identify inconsistent patterns and create a unit test based "
                                      "on these examples",
                       "button": "Save Example"
                   },
                       {
                           "action": "Generate an inconsistency test",
                           "explanation": "This may help you ensure this inconsistent pattern is not common to the "
                                          "whole dataset",
                           "button": "Create test"
                       }
                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]


class StochasticityPush(ExamplePush):
    def __init__(self):
        self._stochasticity()
        # self.test = test_stochasticity @TODO: add this test

    def _stochasticity(self):
        res = {"push_title": "This example generates different predictions at each run",
               "details":
                   [{
                       "action": "Save this example for further inspection and testing",
                       "explanation": "Some stochastic behavior has been found in your model. You may need to fix the "
                                      "random seed of your model",
                       "button": "Save Example"
                   },
                   {
                       "action": "Generate a stochasticity test",
                       "explanation": "This may help you ensure this stochastic pattern is not common to the whole "
                                      "dataset",
                       "button": "Create test"
                   }
                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]


class FeaturePush(Push):
    key = None
    value = None


class ContributionPush(FeaturePush):
    slicing_function = None
    bounds = None
    model_type = None
    correct_prediction = None

    def __init__(self, value=None, feature=None, bounds=None, model_type=None, correct_prediction=None):
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
                       "action": "Open a new debugger session with similar spurious examples",
                       "explanation": "Debugging similar examples may help you find common spurious patterns",
                       "button": "Open debugger"
                   },
                       {
                           "action": "Generate a new performance difference test",
                           "explanation": "This may help ensure this spurious pattern is not common to the whole "
                                          "dataset",
                           "button": "Create test"
                       },
                       {
                           "action": "Save slice and continue debugging session",
                           "explanation": "Saving the slice will enable you to create tests more efficiently",
                           "button": "Save Slice"
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
                       "action": "Open a new debugger session with similar examples",
                       "explanation": "Debugging similar examples may help you find common patterns",
                       "button": "Open debugger"
                   },
                       {
                           "action": "Generate a test to check if this correlation holds with the whole dataset",
                           "explanation": "Correlations may be spurious, double check if it has a business sense",
                           "button": "Create test"
                       },
                       {
                           "action": "Save slice and continue debugging session",
                           "explanation": "Saving the slice will enable you to create tests more efficiently",
                           "button": "Save Slice"
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

    def __init__(self, value=None, feature=None, text_perturbed=None, transformation_function=None):
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
                       "button": "Create test"
                   },
                       {
                           "action": "Save the perturbation that made the model change and continue debugging session",
                           "explanation": "Saving this perturbation will enable you to create tests more efficiently",
                           "button": "Save Perturbation"
                       }
                   ]
               }

        self.push_title = res["push_title"]
        self.details = res["details"]
        return res
