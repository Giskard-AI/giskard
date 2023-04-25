import ml_worker_pb2


class Perturbation:
    def __init__(self, passed, perturbation_value):
        self.passed = passed
        self.perturbation_value = perturbation_value


class Push:
    key = None
    value = None
    push_title = None
    push_details = None
    perturbation_value = None

    def __init__(self, push_type, feature, value, perturbation_value=None):
        self.perturbation_value = perturbation_value
        self.key = feature
        self.value = value
        if push_type == "contribution_wrong":
            self._high_contribution_wrong_prediction(feature, value)

        if push_type == "contribution_only":
            self._high_contribution_only(feature, value)
        if push_type == "perturbation":
            self._perturbation(feature, value)

    def _high_contribution_wrong_prediction(self, feature, value):
        res = {"push_title": f"{str(feature)}=={str(value)} is responsible for the incorrect prediction",
               "push_details":
                   [{
                       "action": "Open a new debugger session with similar spurious examples",
                       "explanation": "Debugging similar examples may help you find common spurious patterns",
                       "button": "Open debugger"
                   },
                       {
                           "action": "Generate a new performance difference test in the catalog",
                           "explanation": "This may help ensure this spurious pattern is not common to the whole dataset",
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
        self.push_details = res["push_details"]
        return res

    def _high_contribution_only(self, feature, value):
        res = {"push_title": f"{str(feature)}=={str(value)} contributes a lot to the prediction",
               "push_details":
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
        self.push_details = res["push_details"]
        return res

    def _perturbation(self, feature, value):
        res = {"push_title": f"A small variation of {str(feature)}=={str(value)} makes the prediction change",
               "push_details":
                   [{
                       "action": "Generate a robustness test in the catalog that slightly perturb this feature",
                       "explanation": "This will enable you to make sure the model is robust against small similar changes",
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
        self.push_details = res["push_details"]
        return res

    def to_grpc(self):
        return ml_worker_pb2.Push(
            key=self.key,
            value=self.value,
            push_title=self.push_title,
            push_details=self.push_details,
            perturbation_value=self.perturbation_value
        )
