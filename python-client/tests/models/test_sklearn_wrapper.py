import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from giskard.models.sklearn import SKLearnModel


def test_must_provide_feature_names_if_has_preprocessing():
    df = pd.DataFrame({"a": np.random.normal(size=100), "b": np.random.normal(size=100)})
    reg = LinearRegression()
    reg.fit(df, np.ones(100))

    with pytest.raises(ValueError):
        SKLearnModel(reg, model_type="regression", data_preprocessing_function=lambda df: df)

    assert SKLearnModel(reg, model_type="regression", feature_names=["test"], data_preprocessing_function=lambda df: df)


def test_raises_save_error_if_unknown_model_type():
    reg = LinearRegression()
    gsk_model = SKLearnModel(reg, model_type="regression")

    with pytest.raises(ValueError):
        gsk_model.meta.model_type = "unknown"
        gsk_model.save_model("test_path", None)
