import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from giskard import Model
from giskard.core.core import SupportedModelTypes


def test_catboost(german_credit_test_data, german_credit_catboost):
    res = german_credit_catboost.predict(german_credit_test_data)
    assert len(res.prediction) == len(german_credit_test_data.df)
    assert (res.probabilities >= 0).all() and (res.probabilities <= 1).all()


def test_catboost_changed_column_order(german_credit_test_data, german_credit_catboost):
    original_predictions = german_credit_catboost.predict(german_credit_test_data).probabilities

    # change column order
    df = german_credit_test_data.df
    german_credit_test_data.df = df.reindex(df.columns[::-1], axis=1)

    # reset feature names to test the behaviour when they're not provided
    german_credit_catboost.feature_names = None

    res = german_credit_catboost.predict(german_credit_test_data)
    assert len(res.prediction) == len(german_credit_test_data.df)
    assert (res.probabilities >= 0).all() and (res.probabilities <= 1).all()
    assert np.array_equal(
        german_credit_catboost.predict(german_credit_test_data).probabilities,
        original_predictions,
    ), "Predictions are not the same after changing features order"


def test_prediction_cache_loaded_model(linear_regression_diabetes, linear_regression_diabetes_raw, diabetes_dataset):
    nb_of_prediction_calls = [0]

    def prediction_fn(df):
        nb_of_prediction_calls[0] += 1
        return np.ones(df.shape[0])

    with tempfile.TemporaryDirectory(prefix="cache_dir-") as cache_dir, tempfile.TemporaryDirectory(
        prefix="model_dir-"
    ) as model_dir:
        model = Model(
            prediction_fn,
            model_type=SupportedModelTypes.REGRESSION,
            feature_names=linear_regression_diabetes.meta.feature_names,
            prediction_cache_dir=Path(cache_dir),
        )

        predictions = model.predict(diabetes_dataset)
        model.save(model_dir)

        loaded_model = Model.load(model_dir, prediction_cache_dir=Path(cache_dir))
        second_predictions = loaded_model.predict(diabetes_dataset)

        assert np.all(np.equal(predictions.raw, second_predictions.raw))
        assert nb_of_prediction_calls[0] == 1


def test_model_save_and_load_not_overriden():
    def model_fn(df):
        return [True] * len(df)

    call_count = dict({"save": 0, "load": 0})

    class MyCustomModel(Model):
        def save_model(self, path):
            call_count["save"] = call_count["save"] + 1
            Path(path).joinpath("custom_data").touch()

        @classmethod
        def load_model(cls, path, **kwargs):
            call_count["load"] = call_count["load"] + 1

            def model(x):
                return [True] * len(x)

            return model

        def model_predict(self, df: pd.DataFrame):
            return self.model(df)

    with tempfile.TemporaryDirectory() as tmpdirname:
        gsk_model = MyCustomModel(model_fn, model_type="regression")

        gsk_model.save(tmpdirname)
        assert call_count["save"] == 1

        MyCustomModel.load(tmpdirname)
        assert call_count["load"] == 1
