import pytest
import pandas as pd
import numpy as np

from giskard import Dataset
from giskard.slicing.slice import QueryBasedSliceFunction
from giskard.slicing.slice import GreaterThan, LowerThan
from giskard.slicing.text_slicer import TextSlicer
from giskard.slicing.tree_slicer import DecisionTreeSlicer


def _make_demo_dataset(**kwargs):
    feature1 = np.arange(1000)
    loss = np.zeros(1000)
    loss[0:200] = 2
    loss[500:600] = 1
    # Shuld create 4 slices:
    # - feature1 <= 199.5
    # - 199.5 < feature1 <= 499.5
    # - 499.5 < feature1 <= 599.5
    # - feature1 > 599.5

    df = pd.DataFrame({"feature1": feature1, "loss": loss})

    return Dataset(df, **kwargs)


def _get_slice_interval(slice_fn: QueryBasedSliceFunction, column: str):
    clauses = slice_fn.query.clauses[column]

    try:
        low = max(c.value for c in clauses if isinstance(c, GreaterThan))
    except (StopIteration, ValueError):
        low = None

    try:
        high = min(c.value for c in clauses if isinstance(c, LowerThan))
    except (StopIteration, ValueError):
        high = None

    return low, high


@pytest.mark.parametrize(
    "slicer_cls",
    [DecisionTreeSlicer],
)
def test_slicer_on_numerical_feature(slicer_cls):
    dataset = _make_demo_dataset()
    slicer = slicer_cls(dataset)
    slices = slicer.find_slices(features=["feature1"], target="loss")

    assert len(slices) == 4
    for s in slices:
        assert isinstance(s, QueryBasedSliceFunction)

    intervals = [_get_slice_interval(s, "feature1") for s in slices]
    intervals = sorted(intervals, key=lambda x: (x[0] or -np.inf, x[1] or np.inf))

    assert intervals[0][0] is None
    assert intervals[0][1] == pytest.approx(199.5, abs=1)

    assert intervals[1][0] == pytest.approx(199.5, abs=1)
    assert intervals[1][1] == pytest.approx(499.5, abs=1)

    assert intervals[2][0] == pytest.approx(499.5, abs=1)
    assert intervals[2][1] == pytest.approx(599.5, abs=1)

    assert intervals[3][0] == pytest.approx(599.5, abs=1)
    assert intervals[3][1] is None


def test_text_slicer_enforces_cast_to_string():
    dataset = _make_demo_dataset(column_types={"feature1": "text", "loss": "numeric"})

    slicer = TextSlicer(dataset)
    slices = slicer.find_metadata_slices("feature1", "loss")
    assert len(slices) > 0


def test_text_slicer_warns_if_vocabulary_is_empty():
    df = pd.DataFrame({"feature1": ["and", "", "and", "to"], "loss": [1, 2, 1, 2]})
    dataset = Dataset(df)
    slicer = TextSlicer(dataset)
    with pytest.warns(match="Could not get meaningful tokens"):
        slices = slicer.find_token_based_slices("feature1", "loss")

    assert len(slices) == 0


def test_text_slicer_does_not_fail_when_loss_is_constant():
    df = pd.DataFrame(
        {
            "text": ["All that is solid", "melts into air", "Все твердое растворяется в воздухе"] * 100,
            "loss": [1, 1, 1] * 100,
        }
    )
    dataset = Dataset(df)
    slicer = TextSlicer(dataset)
    slices = slicer.find_slices(["text"], "loss")

    assert len(slices) > 0
