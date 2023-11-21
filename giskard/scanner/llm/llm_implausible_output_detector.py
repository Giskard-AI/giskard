from typing import Sequence

import pandas as pd

from giskard.scanner import logger

from ...datasets.base import Dataset
from ...llm.evaluators import PlausibilityEvaluator
from ...llm.generators import ImplausibleDataGenerator
from ...models.base.model import BaseModel
from ...testing.tests.llm.hallucination import test_llm_output_plausibility
from ..decorators import detector
from ..issues import Hallucination, Issue, IssueLevel
from ..registry import Detector
from .base import _estimate_base_token_counts


@detector(
    "llm_implausible_output",
    tags=["hallucination", "misinformation", "implausible_output", "llm", "generative", "text_generation"],
)
class LLMImplausibleOutputDetector(Detector):
    """Detects implausible output in LLM-based models.

    The detector will stimulate the model in producing outputs that are implausible or controversial by generating a
    set of ad hoc adversarial inputs. This can be seen as a proxy for hallucination and misinformation detection.
    """

    def __init__(self, num_samples=10):
        self.num_samples = num_samples

    def get_cost_estimate(self, model: BaseModel, dataset: Dataset) -> dict:
        counts = _estimate_base_token_counts(model, dataset)
        model_meta_tokens = counts["model_meta_tokens"]
        input_sample_tokens = counts["input_sample_tokens"]

        num_calls = 0
        num_prompt_tokens = 0
        num_sampled_tokens = 0

        # Data generation
        num_calls += 1
        num_prompt_tokens += 340 + model_meta_tokens
        num_sampled_tokens += input_sample_tokens * self.num_samples

        # Evaluation, for each generated sample
        num_calls += self.num_samples
        num_prompt_tokens += self.num_samples * (180 + model_meta_tokens + input_sample_tokens + 50)
        num_sampled_tokens += self.num_samples * 15

        return {
            "model_predict_calls": self.num_samples,
            "llm_calls": num_calls,
            "llm_prompt_tokens": num_prompt_tokens,
            "llm_sampled_tokens": num_sampled_tokens,
        }

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
                    taxonomy=["avid-effect:performance:P0204"],
                )
            ]

        return []


def _generate_implausible_output_tests(issue: Issue):
    return {"Output plausibility": test_llm_output_plausibility(dataset=issue.dataset)}
