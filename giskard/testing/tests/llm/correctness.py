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
def test_llm_correctness(model: BaseModel, dataset: Dataset, threshold: float = 0.5, rng_seed: int = 1729):
    """Tests if LLM answers are correct with respect to a known reference answers.

    The test is passed when the ratio of correct answers is higher than the
    threshold.

    Parameters
    ----------
    model : BaseModel
        Model used to compute the test
    dataset : Dataset
        Dataset used to compute the test
    threshold : float
        The threshold value for the ratio of invariant rows.

    Returns
    -------
    TestResult
        A TestResult object containing the test result.
    """
    correctness_evaluator = CorrectnessEvaluator(llm_seed=rng_seed)
    eval_result = correctness_evaluator.evaluate(model, dataset)
    output_ds = list()

    if not eval_result.passed:
        failed_indices = [s["sample"]["meta"]["__sample_id"] for s in eval_result.failure_examples]

        output_ds.append(dataset.slice(lambda df: df.loc[failed_indices], row_level=False))

    passed = eval_result.passed_ratio > threshold

    return TestResult(
        passed=passed,
        metric=eval_result.passed_ratio,
        metric_name="Failing examples ratio",
        is_error=eval_result.has_errors,
        details=eval_result.details,
        output_ds=output_ds,
    )
