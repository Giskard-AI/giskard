from typing import Optional

import json

from pydantic import BaseModel

from giskard.core.core import CallableMeta
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.utils import Direction
from giskard.push.push_test_catalog.catalog import test_diff_rmse_push


def test_func(model) -> None:
    """Some test func

    Parameters
    ----------
    model :
        some params
    """
    pass


def test_func_doc_google(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 0.1,
    direction: Direction = Direction.Decreasing,
) -> str:
    """Test for difference in RMSE between a slice and full dataset.

    Checks if the RMSE on a sliced subset of the data is significantly
    different from the full dataset based on a threshold and direction.

    Can be used with pushes to test if problematic slices have worse RMSE.

    Args:
        model (BaseModel): Model to test
        dataset (Dataset): Full dataset
        slicing_function (Optional[SlicingFunction], optional): Function to slice dataset. Defaults to None.
        threshold (float, optional): Allowed RMSE difference. Defaults to 0.1.
        direction (Direction, optional): Whether slice RMSE should increase or decrease. Defaults to Direction.Decreasing.

    """
    return "OK"


def test_extract_doc(caplog):
    doc = CallableMeta.extract_doc(test_diff_rmse_push)
    params = json.loads(doc)
    assert "Test for difference in RMSE between a slice and full dataset" in params["description"]
    assert {"model", "dataset", "slicing_function", "threshold", "direction"} == set(params["parameters"].keys())

    assert caplog.text == ""


def test_extract_doc_warnings(caplog):
    doc = CallableMeta.extract_doc(test_func)
    params = json.loads(doc)
    assert "test_func is missing type hinting for params model" in caplog.text


def test_extract_doc_google(caplog):
    doc = CallableMeta.extract_doc(test_func_doc_google)
    params = json.loads(doc)
    assert "Test for difference in RMSE between a slice and full dataset" in params["description"]
    assert {"model", "dataset", "slicing_function", "threshold", "direction"} == set(params["parameters"].keys())
    assert caplog.text == ""
