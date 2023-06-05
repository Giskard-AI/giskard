from typing import Optional
import pandas as pd
from giskard import test
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.test_result import TestResult
from giskard.models.base import BaseModel


def test_execution_gets_correct_arguments(german_credit_model):
    # Simplest test
    @test
    def my_simple_test(model: BaseModel, threshold: float = 0.5):
        return TestResult(passed=True)

    my_test = my_simple_test(german_credit_model, 0.10)

    assert my_test.meta.args["model"].argOrder == 0
    assert my_test.meta.args["threshold"].argOrder == 1

    # Custom test
    @test
    def my_custom_test(
        model: BaseModel, data: pd.DataFrame, slicing_fn: Optional[SlicingFunction] = None, threshold: float = 0.5
    ):
        return TestResult(passed=True)

    demo_df = pd.DataFrame()
    my_test = my_custom_test(german_credit_model, demo_df, threshold=0.10)
    my_test.execute()

    assert my_test.meta.args["model"].argOrder == 0
    assert my_test.meta.args["data"].argOrder == 1
    assert my_test.meta.args["slicing_fn"].argOrder == 2
    assert my_test.meta.args["threshold"].argOrder == 3
