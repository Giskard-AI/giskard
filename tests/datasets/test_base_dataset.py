import uuid

import pandas as pd
import pytest

from giskard import Dataset


@pytest.fixture
def df() -> pd.DataFrame:
    return pd.DataFrame({"a": range(10), "b": ["x", "y"] * 5})


def test_named_and_IDed_dataset_str(df: pd.DataFrame):
    uid = uuid.uuid4()
    dataset = Dataset(name="foo", id=uid, df=df)
    assert str(dataset) == f"foo({uid})"


def test_named_dataset_str(df: pd.DataFrame):
    dataset = Dataset(name="bar", df=df)
    assert str(dataset).split("(")[0] == "bar"


def test_unnamed_dataset_str(df: pd.DataFrame):
    dataset = Dataset(df=df)
    assert hex(id(dataset)).lower()[2:] in str(dataset).lower()
    assert "<giskard.datasets.base.Dataset object at" in str(dataset)


def test_repr_named_dataset(df: pd.DataFrame):
    dataset = Dataset(name="bar", df=df)
    assert hex(id(dataset)).lower()[2:] in repr(dataset).lower()
    assert "<giskard.datasets.base.Dataset object at" in repr(dataset)


def test_empty_df(df: pd.DataFrame):
    dataset = Dataset(name="bar", df=pd.DataFrame(), feature_names=["test"])
    assert len(dataset.df) == 0
