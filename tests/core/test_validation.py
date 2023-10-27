import math

import pytest
from pydantic import ValidationError

from giskard.core.validation import ConfiguredBaseModel


def test_model_forbid_extra():
    class TestModel(ConfiguredBaseModel):
        a: str
        b: int

    TestModel(a="toot", b=5)
    with pytest.raises(ValidationError) as exc_info:
        TestModel(a="toto", b=5, c=True)
    assert "Extra inputs are not permitted" in str(exc_info)

    with pytest.raises(ValidationError) as exc_info:
        TestModel.parse_obj({"a": "toto", "b": 5, "c": True})
    assert "Extra inputs are not permitted" in str(exc_info)


def test_model_forbid_inf_nan():
    class TestModel(ConfiguredBaseModel):
        a: float

    TestModel(a=5.0)
    with pytest.raises(ValidationError) as exc_info:
        TestModel(a=math.inf)
    assert "Input should be a finite number" in str(exc_info)

    with pytest.raises(ValidationError) as exc_info:
        TestModel.parse_obj({"a": math.nan})
    assert "Input should be a finite number" in str(exc_info)
