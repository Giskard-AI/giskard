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
def test_llm_correctness(model: BaseModel, dataset: Dataset):
    correctness_evaluator = CorrectnessEvaluator()
    eval_result = correctness_evaluator.evaluate(model, dataset)

    return TestResult(
        passed=eval_result.passed,
        metric=len(eval_result.failure_examples),
        metric_name="Failing examples",
        is_error=eval_result.has_errors,
        details=eval_result.details,
    )
