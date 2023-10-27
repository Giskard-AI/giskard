import math

import pydantic
import pytest
from packaging import version
from pydantic import ValidationError

from giskard.core.validation import ConfiguredBaseModel

IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")


def test_model_forbid_extra():
    class TestModel(ConfiguredBaseModel):
        a: str
        b: int

    TestModel(a="toot", b=5)
    with pytest.raises(ValidationError) as exc_info:
        TestModel(a="toto", b=5, c=True)

    with pytest.raises(ValidationError) as exc_info:
        TestModel.parse_obj({"a": "toto", "b": 5, "c": True})
    if IS_PYDANTIC_V2:
        assert "Extra inputs are not permitted" in str(exc_info)
    else:
        assert "extra fields not permitted" in str(exc_info)


def test_model_forbid_inf_nan():
    class TestModel(ConfiguredBaseModel):
        a: float

    TestModel(a=5.0)
    with pytest.raises(ValidationError) as exc_info:
        TestModel(a=math.inf)

    if IS_PYDANTIC_V2:
        assert "Input should be a finite number" in str(exc_info)
    else:
        assert "ensure this value is a finite number" in str(exc_info)
