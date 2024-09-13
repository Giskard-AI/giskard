import uuid

import numpy as np
import pandas as pd
import pytest

from giskard.models.base.model import BaseModel

MANDATORY_FIELDS = [
    "id",
    "name",
    "modelType",
    "featureNames",
    "languageVersion",
    "language",
    "createdDate",
    "size",
    "projectId",
]
OPTIONAL_FIELDS = [
    "threshold",
    "description",
    "classificationLabels",
    "classificationLabelsDtype",
]


class _CustomModel(BaseModel):
    def predict_df(self, df: pd.DataFrame, *args, **kwargs):
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


def test_named_and_IDed_model_str():
    uid = str(uuid.uuid4())
    model = _CustomModel(name="foo", model_type="regression", id=uid)
    assert str(model) == f"foo({uid})"


def test_named_model_str():
    model = _CustomModel(name="bar", model_type="regression")
    assert str(model).split("(")[0] == "bar"


def test_unnamed_model_str():
    model = _CustomModel(model_type="regression")
    assert str(model).split("(")[0] == "_CustomModel"


def test_repr_named_model():
    model = _CustomModel(model_type="regression")
    assert hex(id(model)).lower()[2:] in repr(model).lower()
    assert "<test_base_model._CustomModel object at" in repr(model)
