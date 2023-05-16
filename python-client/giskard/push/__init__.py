from giskard.ml_worker.generated import ml_worker_pb2
from giskard.slicing.slice import GreaterThan, LowerThan, EqualTo, Query, QueryBasedSliceFunction
from enum import Enum
from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.testing.tests.performance import test_f1, test_rmse


class SupportedPerturbationType(Enum):
    NUMERIC = "numeric"
    TEXT = "text"


class Push:
    key = None
    value = None  # list of numerical value or category

    push_title = None
    details = None

    selected_test = None
    _model_type = None

    slicing_function = None
    bounds = None
    text_perturbed: list = None
    transformation_function: list = None

    def __init__(self, push_type, value=None, feature=None, bounds=None, model_type=None,
                 text_perturbed=None, transformation_function=None):
        self.key = feature
        self.value = value
        self.bounds = bounds
        self._model_type = model_type
        self.text_perturbed = text_perturbed
        self.transformation_function = transformation_function
        if push_type == "contribution_wrong":
            self._high_contribution_wrong_prediction(feature, value)
        if push_type == "contribution_only":
            self._high_contribution_only(feature, value)
        if push_type == "perturbation":
            self._perturbation(feature, value)
        if push_type == "overconfidence":
            self._overconfidence()
        if push_type == "borderline":
            self._borderline()
        if push_type == "stochasticity":
            self._stochasticity()
        self._slicing_function()
        self.test_selection()

    def to_grpc(self):
        return ml_worker_pb2.Push(
            key=self.key,
            value=str(self.value),
            push_title=self.push_title,
            push_details=self.details,
        )

    def test_selection(self):
        if self._model_type == SupportedModelTypes.REGRESSION:
            self.selected_test = test_f1
        elif self._model_type == SupportedModelTypes.CLASSIFICATION:
            self.selected_test = test_rmse

    def _high_contribution_wrong_prediction(self, feature, value):
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

    def _high_contribution_only(self, feature, value):
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

        # Details about the perturbation for textual feature - Transforming into upper-case, Shuffeling ,
        # Swapping tokens makes the prediction change
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

    def _stochasticity(self):
        res = {"push_title": "This example generates different predictions at each run",
               "details":
                   [{
                       "action": "Save this example for further inspection and testing",
                       "explanation": "Some stochastic behavior has been found in your model. You may need to fix the "
                                      "random seed of your model",
                       "button": "Save Example"
                   }
                   ]
               }
        self.push_title = res["push_title"]
        self.details = res["details"]
