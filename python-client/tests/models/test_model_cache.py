import numpy as np
import pandas as pd

from giskard import Dataset
from giskard import Model


def test_predict_once():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df.values)

    wrapped_model = Model(
        prediction_function,
        model_type="regression"
    )

    wrapped_dataset = Dataset(
        df=pd.DataFrame([0, 1])
    )

    prediction = wrapped_model.predict(wrapped_dataset)
    cached_prediction = wrapped_model.predict(wrapped_dataset)

    assert called_indexes == list(wrapped_dataset.df.index), 'The  prediction should have been called once'
    assert list(prediction.raw) == list(cached_prediction.raw)
    assert list(prediction.raw_prediction) == list(cached_prediction.raw_prediction)
    assert list(prediction.prediction) == list(cached_prediction.prediction)
    assert prediction.probabilities == cached_prediction.probabilities


def test_predict_disabled_cache():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df.values)

    wrapped_model = Model(
        prediction_function,
        model_type="regression"
    )
    wrapped_model.disable_cache = True

    wrapped_dataset = Dataset(
        df=pd.DataFrame([0, 1])
    )

    prediction = wrapped_model.predict(wrapped_dataset)
    second_prediction = wrapped_model.predict(wrapped_dataset)

    assert called_indexes == list(wrapped_dataset.df.index) + list(
        wrapped_dataset.df.index), 'The prediction should have been called twice'
    assert list(prediction.raw) == list(second_prediction.raw)
    assert list(prediction.raw_prediction) == list(second_prediction.raw_prediction)
    assert list(prediction.prediction) == list(second_prediction.prediction)
    assert prediction.probabilities == second_prediction.probabilities


def test_predict_only_recompute_transformed_values():
    called_indexes = []

    def prediction_function(df: pd.DataFrame) -> np.ndarray:
        called_indexes.extend(df.index)
        return np.array(df.values)

    wrapped_model = Model(
        prediction_function,
        model_type="regression"
    )

    wrapped_dataset = Dataset(
        df=pd.DataFrame([0, 1])
    )

    prediction = wrapped_model.predict(wrapped_dataset)

    def replace_row_one(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[1, 0] = 2
        return df

    transformed_dataset = wrapped_dataset.transform(replace_row_one, row_level=False)
    second_prediction = wrapped_model.predict(transformed_dataset)

    assert called_indexes == list(wrapped_dataset.df.index) + [
        1], 'The  prediction should have been called once for row 0 and twice of row 2'
    assert list(prediction.raw) != list(second_prediction.raw)
    assert list(prediction.raw_prediction) != list(second_prediction.raw_prediction)
    assert list(prediction.prediction) != list(second_prediction.prediction)
