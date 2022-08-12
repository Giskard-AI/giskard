import numpy as np
import pytest


def test_catboost(german_credit_test_data, german_credit_catboost):
    res = german_credit_catboost.run_predict(german_credit_test_data)
    assert len(res.prediction) == len(german_credit_test_data.df)
    assert (res.probabilities >= 0).all() and (res.probabilities <= 1).all()


@pytest.mark.skip(reason="GSK-230 enable test once model upload API is changed from functional to class based")
def test_catboost_changed_column_order(german_credit_test_data, german_credit_catboost):
    original_predictions = german_credit_catboost.run_predict(german_credit_test_data).probabilities

    # change column order
    df = german_credit_test_data.df
    german_credit_test_data.df = df.reindex(df.columns[::-1], axis=1)

    # reset feature names to test the behaviour when they're not provided
    german_credit_catboost.feature_names = None

    res = german_credit_catboost.run_predict(german_credit_test_data)
    assert len(res.prediction) == len(german_credit_test_data.df)
    assert (res.probabilities >= 0).all() and (res.probabilities <= 1).all()
    assert np.array_equal(german_credit_catboost.run_predict(german_credit_test_data).probabilities,
                          original_predictions), "Predictions are not the same after changing features order"
