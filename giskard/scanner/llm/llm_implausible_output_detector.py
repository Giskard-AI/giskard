from typing import Sequence

import pandas as pd

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.evaluators import PlausibilityEvaluator
from ...llm.generators import ImplausibleDataGenerator
from ...models.base.model import BaseModel
from ...testing.tests.llm.hallucination import test_llm_plausibility
from ..decorators import detector
from ..issues import Hallucination, Issue, IssueLevel


@detector(
    "llm_implausible_output",
    tags=["hallucination", "misinformation", "implausible_output", "llm", "generative", "text_generation"],
)
class LLMImplausibleOutputDetector:
    def __init__(self, num_samples=10):
        self.num_samples = num_samples

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        # Generate inputs
        generator = ImplausibleDataGenerator(llm_temperature=0.1)
        eval_dataset = generator.generate_dataset(
            model, num_samples=self.num_samples, column_types=dataset.column_types
        )
        logger.debug(f"{self.__class__.__name__}: Generated {len(eval_dataset)} inputs")

        # Evaluate the model outputs
        evaluator = PlausibilityEvaluator()
        eval_result = evaluator.evaluate(model, eval_dataset)

        if eval_result.failed:
            return [
                Issue(
                    model,
                    eval_dataset,
                    group=Hallucination,
                    level=IssueLevel.MEDIUM,
                    description="The model produces implausible output.",
                    meta={
                        "domain": "Implausible or controversial output",
                        "deviation": "The model produces implausible output.",
                        "hide_index": True,
                    },
                    examples=pd.DataFrame(eval_result.failure_examples),
                    tests=_generate_implausible_output_tests,
                )
            ]

        return []


def _generate_implausible_output_tests(issue: Issue):
    return {"Output plausibility": test_llm_plausibility(model=issue.model, dataset=issue.dataset)}
