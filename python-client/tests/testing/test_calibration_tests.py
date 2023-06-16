import numpy as np
import pandas as pd
from pytest import approx

from giskard.datasets.base import Dataset
from giskard import slicing_function
from giskard.models.automodel import Model
from giskard.testing.tests.calibration import (
    _calculate_overconfidence_score,
    _calculate_underconfidence_score,
    test_overconfidence_rate,
    test_underconfidence_rate,
)


def _make_model_and_data_overconfidence():
    predictions = [[0.1, 0.9], [0.2, 0.8], [0.4, 0.6]]
    data = Dataset(pd.DataFrame({"feature": np.random.normal(size=3), "target": [1, 0, 0]}), target="target")
    model = Model(
        lambda df: np.asarray(predictions)[: len(df)], model_type="classification", classification_labels=[0, 1]
    )

    return model, data


def test_overconfidence_score():
    model, data = _make_model_and_data_overconfidence()

    scores = _calculate_overconfidence_score(model, data).tolist()

    assert scores[0] == 0.0
    assert scores[1] == approx(0.6)
    assert scores[2] == approx(0.2)

    predictions = [[0.1, 0.7, 0.2], [0.3, 0.6, 0.1], [0.4, 0.5, 0.1]]
    data = Dataset(pd.DataFrame({"feature": np.random.normal(size=3), "target": [0, 1, 0]}), target="target")
    model = Model(lambda df: np.asarray(predictions), model_type="classification", classification_labels=[0, 1, 2])

    scores = _calculate_overconfidence_score(model, data).tolist()

    assert scores[0] == approx(0.6)
    assert scores[1] == 0.0
    assert scores[2] == approx(0.1)


def test_overconfidence_rate_threshold():
    model, data = _make_model_and_data_overconfidence()
    t = test_overconfidence_rate(model, data, threshold=0.6)
    res = t.execute()

    assert res.passed
    assert res.metric == approx(0.5)

    t = test_overconfidence_rate(model, data, threshold=0.4)
    res = t.execute()

    assert not res.passed


def test_overconfidence_rate_slicing():
    model, data = _make_model_and_data_overconfidence()

    @slicing_function(row_level=False)
    def keep_two(df):
        return df.head(2)

    t = test_overconfidence_rate(model, data, slicing_function=keep_two, threshold=0.6)
    res = t.execute()

    assert not res.passed
    assert res.metric == approx(1.0)


def test_overconfidence_rate_p_threshold():
    model, data = _make_model_and_data_overconfidence()
    t = test_overconfidence_rate(model, data, threshold=0.6, p_threshold=0.1)
    res = t.execute()

    assert not res.passed
    assert res.metric == approx(1.0)

    t = test_overconfidence_rate(model, data, threshold=0.6, p_threshold=0.99)
    res = t.execute()

    assert res.passed
    assert res.metric == approx(0.0)


def _make_model_and_data_underconfidence():
    predictions = [[0.49, 0.51], [0.2, 0.8], [0.475, 0.525], [0.1, 0.9]]
    data = Dataset(pd.DataFrame({"feature": np.random.normal(size=4), "target": [1, 0, 0, 1]}), target="target")
    model = Model(
        lambda df: np.asarray(predictions)[: len(df)], model_type="classification", classification_labels=[0, 1]
    )

    return model, data


def test_underconfidence_score():
    model, data = _make_model_and_data_underconfidence()

    scores = _calculate_underconfidence_score(model, data).tolist()

    assert scores[0] == approx(49 / 51)
    assert scores[1] == approx(2 / 8)
    assert scores[2] == approx(475 / 525)
    assert scores[3] == approx(1 / 9)

    predictions = [[0.1, 0.7, 0.2], [0.3, 0.6, 0.1], [0.4, 0.5, 0.1]]
    data = Dataset(pd.DataFrame({"feature": np.random.normal(size=3), "target": [0, 1, 0]}), target="target")
    model = Model(lambda df: np.asarray(predictions), model_type="classification", classification_labels=[0, 1, 2])

    scores = _calculate_underconfidence_score(model, data).tolist()

    assert scores[0] == approx(2 / 7)
    assert scores[1] == approx(3 / 6)
    assert scores[2] == approx(4 / 5)


def test_underconfidence_rate_threshold():
    model, data = _make_model_and_data_underconfidence()
    t = test_underconfidence_rate(model, data, threshold=0.6)
    res = t.execute()

    assert res.passed
    assert res.metric == approx(0.5)

    t = test_underconfidence_rate(model, data, threshold=0.4)
    res = t.execute()

    assert not res.passed


def test_underconfidence_rate_slicing():
    model, data = _make_model_and_data_underconfidence()

    @slicing_function(row_level=False)
    def keep_three(df):
        return df.head(3)

    t = test_underconfidence_rate(model, data, slicing_function=keep_three, threshold=0.6)
    res = t.execute()

    assert not res.passed
    assert res.metric == approx(2 / 3)


def test_underconfidence_rate_p_threshold():
    model, data = _make_model_and_data_underconfidence()

    t = test_underconfidence_rate(model, data, threshold=0.5, p_threshold=0.95)
    res = t.execute()

    assert res.passed
    assert res.metric == approx(1 / 4)

    t = test_underconfidence_rate(model, data, threshold=0.6, p_threshold=0.90)
    res = t.execute()

    assert res.passed
    assert res.metric == approx(2 / 4)

    t = test_underconfidence_rate(model, data, threshold=0.6, p_threshold=0.01)
    res = t.execute()

    assert not res.passed
    assert res.metric == approx(1)
