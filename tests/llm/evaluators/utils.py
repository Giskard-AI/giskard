from unittest.mock import Mock

import pandas as pd

from giskard.datasets.base import Dataset
from giskard.models.base.model_prediction import ModelPredictionResults


def make_eval_dataset():
    return Dataset(
        pd.DataFrame(
            {
                "question": ["What is your favourite color?", "What is the airspeed velocity of an unladen swallow?"],
                "other": ["pass", "pass"],
            }
        )
    )


def make_mock_model():
    model = Mock()
    model.predict.return_value = ModelPredictionResults(
        prediction=["Blue", "What do you mean? An African or European swallow?"]
    )
    model.feature_names = ["question", "other"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"
    return model
