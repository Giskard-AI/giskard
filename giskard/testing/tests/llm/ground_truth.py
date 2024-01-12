import numpy as np

from ....core.test_result import TestResult, TestResultDetails, TestResultStatus
from ....datasets.base import Dataset
from ....llm import LLMImportError
from ....models.base import BaseModel
from ....registry.decorators import test
from .. import debug_description_prefix


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
