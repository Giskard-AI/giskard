import uuid

import pandas as pd
import pytest

from giskard import Dataset


@pytest.fixture
def df():
    return pd.DataFrame({"a": range(10), "b": ["x", "y"] * 5})


def test_named_and_IDed_dataset_str(df):
    uid = uuid.uuid4()
    dataset = Dataset(name="foo", id=uid, df=df)
    assert str(dataset) == f"foo-{uid}"


def test_named_dataset_str(df):
    dataset = Dataset(name="bar", df=df)
    assert str(dataset).split("-")[0] == "bar"


def test_unnamed_dataset_str(df):
    dataset = Dataset(df=df)
    assert str(dataset) == f"<giskard.datasets.base.Dataset object at {hex(id(dataset))}>"
