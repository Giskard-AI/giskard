import numpy as np
import pandas as pd
import pytest

from giskard.models.base.model import BaseModel


class _CustomModel(BaseModel):
    def predict_df(self, df: pd.DataFrame):
        return np.ones(len(df))


def test_base_model_raises_error_for_unknown_model_type():
    assert _CustomModel("regression")  # this is ok

    with pytest.raises(ValueError):
        _CustomModel("invalid")


def test_base_model_raises_error_if_duplicated_target_labels():
    assert _CustomModel("classification", classification_labels=["one", "two"])

    with pytest.raises(ValueError):
        _CustomModel("classification", classification_labels=["one", "two", "one"])


def test_base_model_raises_error_if_classification_labels_not_provided():
    assert _CustomModel("classification", classification_labels=["one", "two"])

    with pytest.raises(ValueError):
        _CustomModel("classification")


# @TODO: add tests for model download
