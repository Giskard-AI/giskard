import numpy as np

from ....core.test_result import TestResult, TestResultDetails, TestResultStatus
from ....datasets.base import Dataset
from ....llm import LLMImportError
from ....llm.evaluators import PerRowRequirementEvaluator
from ....models.base import BaseModel
from ....registry.decorators import test
from .. import debug_description_prefix
from .output_requirements import _test_output_against_requirement


@test(
    name="Evaluation of model output exact match to the ground truth ",
    tags=["llm", "ground-truth"],
    debug_description=debug_description_prefix + "that are <b>generating result differing from ground truth</b>.",
)
def test_llm_ground_truth(model: BaseModel, dataset: Dataset, threshold: float = 0.5):
    if dataset.target is None:
        raise ValueError(f"Provided dataset ({dataset}) does not have any ground truth (target)")

    pred = model.predict(dataset)

    passed = np.array(pred.prediction) == dataset.df[dataset.target]
    metric = len([p for p in passed if p]) / len(passed)

    return TestResult(
        passed=metric >= threshold,
        metric=metric,
        details=TestResultDetails(
            inputs=dataset.df.loc[:, model.meta.feature_names].to_dict("list"),
            outputs=list(pred.prediction),
            results=[TestResultStatus.PASSED if result else TestResultStatus.FAILED for result in passed],
            metadata={"target": list(dataset.df[dataset.target])},
        ),
    )


@test(
    name="Evaluation of model output similarity to the ground truth",
    tags=["llm", "ground-truth"],
    debug_description=debug_description_prefix + "that are <b>generating result differing from ground truth</b>.",
)
def test_llm_ground_truth_similarity(
    model: BaseModel, dataset: Dataset, output_sensitivity: float = 0.15, threshold: float = 0.5, idf: bool = False
):
    if dataset.target is None:
        raise ValueError(f"Provided dataset ({dataset}) does not have any ground truth (target)")

    pred = model.predict(dataset)

    try:
        import evaluate
    except ImportError as err:
        raise LLMImportError() from err

    scorer = evaluate.load("bertscore")
    score = scorer.compute(
        predictions=pred.prediction,
        references=dataset.df[dataset.target],
        model_type="distilbert-base-multilingual-cased",
        idf=idf,
    )
    passed = np.array(score["f1"]) > 1 - output_sensitivity
    metric = len([p for p in passed if p]) / len(passed)

    return TestResult(
        passed=metric >= threshold,
        metric=metric,
        details=TestResultDetails(
            inputs=dataset.df.loc[:, model.meta.feature_names].to_dict("list"),
            outputs=list(pred.prediction),
            results=[TestResultStatus.PASSED if result else TestResultStatus.FAILED for result in passed],
            metadata={"target": list(dataset.df[dataset.target]), "F1 similarity": score["f1"]},
        ),
    )


@test(
    name="Per row evaluation of model output using an LLM (LLM-as-a-judge)",
    tags=["llm", "llm-as-a-judge"],
    debug_description=debug_description_prefix + "that are <b>failing the evaluation criteria</b>.",
)
def test_llm_as_a_judge_ground_truth_similarity(
    model: BaseModel, dataset: Dataset, prefix: str = "The requirement should be similar to: "
):
    """Evaluates the model output against its ground truth  with another LLM (LLM-as-a-judge).

    The model outputs over a given dataset will be validated against the
    dataset target using GPT-4 (note that this requires you to set the
    `OPENAI_API_TOKEN` environment variable for the test to run correctly).

    Parameters
    ----------
    model : BaseModel
        The generative model to test.
    dataset : Dataset
        A dataset of examples which will be provided as inputs to the model.
    prefix : str
        The prefix instructing how the answer should be according to the ground truth”.

    Returns
    -------
    TestResult
        A TestResult object containing the test result.
    """
    if dataset.target is None:
        raise ValueError(f"Provided dataset ({dataset}) does not have any ground truth (target)")

    return _test_output_against_requirement(
        model, dataset, PerRowRequirementEvaluator(dataset.df.loc[:, [dataset.target]], prefix)
    )
