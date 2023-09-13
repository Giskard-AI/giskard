from typing import Optional

from ...datasets.base import Dataset
from ...ml_worker.testing.registry.decorators import test
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...ml_worker.testing.test_result import TestResult
from ...models.base import BaseModel


@test(name="Test case", tags=["llm"])
def test_test_case(
    model: BaseModel,
    dataset: Dataset,
    test_case: str,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 1.0,
):
    from ...llm.utils.validate_test_case import validate_test_case

    if slicing_function is not None:
        dataset = dataset.slice(slicing_function)

    predictions = model.predict(dataset).prediction

    passed = validate_test_case(model, test_case, dataset.df, predictions)
    metric = len([result for result in passed if result]) / len(predictions)

    return TestResult(
        actual_slices_size=[len(dataset)],
        metric=metric,
        passed=bool(metric > threshold),
    )
