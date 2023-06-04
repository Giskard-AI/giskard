import tempfile
import time
from pathlib import Path
from time import perf_counter

import numpy as np
import pytest

from giskard import Model
from giskard.core.core import SupportedModelTypes


def test_catboost(german_credit_test_data, german_credit_catboost):
    res = german_credit_catboost.predict(german_credit_test_data)
    assert len(res.prediction) == len(german_credit_test_data.df)
    assert (res.probabilities >= 0).all() and (res.probabilities <= 1).all()


@pytest.mark.skip(reason="GSK-230 enable test once model upload API is changed from functional to class based")
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


def test_prediction_cache_loaded_model(linear_regression_diabetes, linear_regression_diabetes_raw, diabetes_dataset, request):
    nb_of_prediction_calls = [0]

    def prediction_fn(df):
        # simulate slowish prediction
        time.sleep(1)
        nb_of_prediction_calls[0] += 1
        return np.ones(df.shape[0])

    with tempfile.TemporaryDirectory(prefix="cache_dir-") as cache_dir, \
            tempfile.TemporaryDirectory(prefix="model_dir-") as model_dir:
        model = Model(prediction_fn,
                      model_type=SupportedModelTypes.REGRESSION,
                      feature_names=linear_regression_diabetes.meta.feature_names,
                      prediction_cache_dir=Path(cache_dir))

        start = perf_counter()
        predictions = model.predict(diabetes_dataset)
        first_elapsed = perf_counter() - start
        model.save(model_dir)

        loaded_model = Model.load(model_dir, prediction_cache_dir=Path(cache_dir))
        start = perf_counter()
        second_predictions = loaded_model.predict(diabetes_dataset)
        second_elapsed = perf_counter() - start

        assert np.all(np.equal(predictions.raw, second_predictions.raw))
        assert nb_of_prediction_calls[0] == 1
        # prediction from cache takes at most 5% of the original time
        assert second_elapsed / first_elapsed < 0.05
