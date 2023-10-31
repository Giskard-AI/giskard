from typing import Sequence

import pandas as pd

from ...datasets.base import Dataset
from ...llm.evaluators.coherency import CoherencyEvaluator
from ...llm.generators.sycophancy import SycophancyDataGenerator
from ...models.base.model import BaseModel
from ...testing.tests.llm.hallucination import test_llm_coherency
from ..decorators import detector
from ..issues import Hallucination, Issue, IssueLevel
from ..scanner import logger


@detector(
    "llm_basic_sycophancy",
    tags=["hallucination", "misinformation", "sycophancy", "llm", "generative", "text_generation"],
)
class LLMBasicSycophancyDetector:
    def __init__(self, num_samples=10):
        self.num_samples = num_samples

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # Prepare datasets
        generator = SycophancyDataGenerator()
        dataset1, dataset2 = generator.generate_dataset(
            model, num_samples=self.num_samples, column_types=dataset.column_types
        )
        logger.debug(f"{self.__class__.__name__}: Generated {len(dataset1)} test inputs for model assessment.")

        # Evaluate the answers
        evaluator = CoherencyEvaluator()
        eval_result = evaluator.evaluate(model, dataset1, dataset2)

        if eval_result.failed:
            return [
                Issue(
                    model,
                    dataset2,
                    group=Hallucination,
                    level=IssueLevel.MAJOR,
                    description=(
                        "The model seems to produce contradicting or hallucinated outputs when we provide two sets "
                        "of inputs which are biased in a different way. This is generally a symptom of hallucination "
                        "or sycophancy, i.e. the tendency to produce outputs that agree with the input bias."
                    ),
                    examples=pd.DataFrame(eval_result.failure_examples),
                    meta={
                        "domain": "Sycophancy",
                        "deviation": "The model produces incoherent or hallucinated output when prompted with biased inputs.",
                        "hide_index": True,
                        "dataset_1": dataset1,
                        "dataset_2": dataset2,
                    },
                    tests=_generate_sycophancy_tests,
                )
            ]

        return []


def _generate_sycophancy_tests(issue: Issue):
    return {
        "Basic Sycophancy": test_llm_coherency(
            model=issue.model, dataset_1=issue.meta["dataset_1"], dataset_2=issue.meta["dataset_2"]
        )
    }
