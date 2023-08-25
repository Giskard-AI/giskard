from typing import Optional, Union

import numpy as np
import pandas as pd
import pytest

from giskard import test, slicing_function, transformation_function
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
from giskard.ml_worker.testing.test_result import TestResult as GiskardTestResult
from giskard.models.base import BaseModel


def test_can_define_the_simplest_custom_test(german_credit_model):
    @test
    def my_simple_test(model: BaseModel, threshold: float = 0.5):
        return GiskardTestResult(passed=True)

    my_test = my_simple_test(german_credit_model, 0.10)

    assert my_test.meta.args["model"].argOrder == 0
    assert my_test.meta.args["threshold"].argOrder == 1

    result = my_test.execute()
    assert result.passed


def test_can_define_test_with_optional_type(german_credit_model):
    @test
    def my_optional_test(model: BaseModel, threshold: Optional[float] = None):
        return GiskardTestResult(passed=True)

    my_test = my_optional_test(german_credit_model, 0.10)
    result = my_test.execute()

    assert result.passed

    assert my_test.meta.args["model"].argOrder == 0
    assert my_test.meta.args["threshold"].argOrder == 1

    my_test = my_optional_test(german_credit_model)
    result = my_test.execute()


@pytest.mark.skip(reason="This is not supported yet")
def test_can_define_test_with_union_type(german_credit_model):
    @test
    def my_union_test(model: BaseModel, target: Union[str, int]):
        return GiskardTestResult(passed=True)

    my_test = my_union_test(german_credit_model, "foo")
    result = my_test.execute()

    assert result.passed


@pytest.mark.skip(reason="This is not supported yet")
def test_can_define_test_without_type_hints(german_credit_model, german_credit_data):
    @test
    def my_custom_test(model, data):
        return GiskardTestResult(passed=True)

    my_test = my_custom_test(german_credit_model, german_credit_data)
    result = my_test.execute()
    assert result.passed

    assert my_test.meta.args["model"].argOrder == 0
    assert my_test.meta.args["data"].argOrder == 1


@pytest.mark.skip(reason="This is not supported yet")
def test_can_define_test_with_custom_params(german_credit_model):
    @test
    def my_custom_test(
        model: BaseModel, data: np.ndarray, slicing_fn: Optional[SlicingFunction] = None, threshold: float = 0.5
    ):
        return GiskardTestResult(passed=True)

    my_test = my_custom_test(german_credit_model, np.ones(10), threshold=0.10)
    result = my_test.execute()
    assert result.passed

    assert my_test.meta.args["model"].argOrder == 0
    assert my_test.meta.args["data"].argOrder == 1
    assert my_test.meta.args["slicing_fn"].argOrder == 2
    assert my_test.meta.args["threshold"].argOrder == 3


@pytest.mark.skip(reason="This is not supported yet")
def test_can_define_test_without_type_hints_with_custom_data(german_credit_model):
    @test
    def my_custom_test(model: BaseModel, data, threshold: np.int64, slicing_fn=None):
        return GiskardTestResult(passed=True)

    my_test = my_custom_test(german_credit_model, pd.DataFrame(), 14773)
    my_test.execute()


def test_can_have_default_values_for_giskard_objects():
    @slicing_function()
    def my_slicing_function(df):
        return df

    @transformation_function()
    def my_transformation_function(df):
        return df

    @test()
    def test_with_default(
        sf: SlicingFunction = my_slicing_function, tf: TransformationFunction = my_transformation_function
    ):
        return True

    assert test_with_default.meta.args["tf"].default == my_transformation_function.meta.uuid
    assert test_with_default.meta.args["sf"].default == my_slicing_function.meta.uuid
