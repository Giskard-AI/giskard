import numpy as np
import pandas as pd

import tests.utils
from giskard import Dataset, Model
from giskard.models.function import PredictionFunctionModel


def test_prediction_function_model():
    gsk_model = Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1])
    assert isinstance(gsk_model, PredictionFunctionModel)

    pred = gsk_model.predict(Dataset(df=pd.DataFrame({"x": [1, 2, 3], "y": [1, 1, 0]}), target="y"))

    assert pred.raw.shape == (3, 2)
    assert (pred.raw[:, 1] == 1).all()


def test_prediction_function_upload():
    gsk_model = PredictionFunctionModel(
        lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1]
    )

    tests.utils.verify_model_upload(gsk_model, Dataset(df=pd.DataFrame({"x": [1, 2, 3], "y": [1, 0, 1]}), target="y"))
