from ....core.test_result import TestResult
from ....datasets.base import Dataset
from ....llm.evaluators import CorrectnessEvaluator
from ....models.base import BaseModel
from ....registry.decorators import test
from .. import debug_description_prefix


@test(
    name="LLM Correctness from knowledge base",
    tags=["llm", "llm-as-a-judge"],
    debug_description=debug_description_prefix + "that are <b>failing the evaluation criteria</b>.",
)
def test_llm_correctness(model: BaseModel, dataset: Dataset, threshold: float = 0.5):
    correctness_evaluator = CorrectnessEvaluator()
    eval_result, failed_idx = correctness_evaluator.evaluate(model, dataset)
    output_ds = list()
    if not eval_result.passed:
        output_ds.append(dataset.slice(lambda df: df.loc[failed_idx], row_level=False))

    passed = bool(eval_result.passed_ratio > threshold)

    return TestResult(
        passed=passed,
        metric=eval_result.passed_ratio,
        metric_name="Failing examples ratio",
        is_error=eval_result.has_errors,
        details=eval_result.details,
        output_ds=output_ds,
    )
