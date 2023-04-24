from giskard.core.core import SupportedModelTypes


class Push:
    def __init__(self):
        self.__incorrect = [{
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

        self.__highly_correlated = [{
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

        self.__perturbation = [{
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

    def incorrect(self, feature, value):
        res = {"key": str(feature),
               "value": str(value),
               "push": f"{str(feature)}=={str(value)} is responsible for the incorrect prediction",
               "push_list": self.__incorrect
               }
        return res

    def high_correlation(self, feature, value):
        res = {"key": str(feature),
               "value": str(value),
               "push": f"{str(feature)}=={str(value)} contributes a lot to the prediction",
               "push_list": self.__highly_correlated
               }

        return res

    def perturbation(self, feature, value):
        res = {"key": str(feature),
               "value": str(value),
               "push": f"A small variation of {str(feature)}=={str(value)} makes the prediction change",
               "push_list": self.__perturbation
               }

        # Details about the perturbation for textual feature - Transforming into upper-case, Shuffeling ,
        # Swapping tokens makes the prediction change

        return res
