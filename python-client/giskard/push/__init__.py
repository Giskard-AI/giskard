from giskard.core.core import SupportedModelTypes


class Push:
    def __init__(self):
        self.__incorrect = [{
            "action": "Open a new debugger session with similar examples",
            "explanation": "Debugging similar examples may help you find common patterns",
            "button": "Open debugger"
        },
            {
                "action": "Generate a new performance difference test in the catalog",
                "explanation": "This may help ensure this incorrect pattern is not common to the whole dataset",
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
                "action": "Generate a new drift difference test in the catalog",
                "explanation": "This may help ensure this pattern is not common to the whole dataset",
                "button": "Create test"
            },
            {
                "action": "Save slice and continue debugging session",
                "explanation": "Saving the slice will enable you to create tests more efficiently",
                "button": "Save Slice"
            }
        ]

        self.__perturbation = [{
            "action": "Open a new debugger session with similar examples",
            "explanation": "Debugging similar examples may help you find common patterns",
            "button": "Open debugger"
        },
            {
                "action": "Generate a new metamorphic test in the catalog",
                "explanation": "This may help ensure this pattern is not common to the whole dataset",
                "button": "Create test"
            },
            {
                "action": "Save slice and continue debugging session",
                "explanation": "Saving the slice will enable you to create tests more efficiently",
                "button": "Save Slice"
            }

        ]

    def incorrect(self, feature, value):
        res = {"ke<y": str(feature),
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

    def perturbation(self,feature,value):
        res = {"key": str(feature),
               "value": str(value),
               "push": f"A small variation (+20%) of {str(feature)}=={str(value)} makes the prediction change,"
                       "check if this unrobust behavior generalizes to the whole dataset",
               "push_list": self.__perturbation
               }

        return res
