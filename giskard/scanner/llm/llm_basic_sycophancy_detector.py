from typing import Sequence

import pandas as pd

from ...datasets.base import Dataset
from ...llm.evaluators.coherency import CoherencyEvaluator
from ...llm.generators.sycophancy import SycophancyDataGenerator
from ...models.base.model import BaseModel
from ...testing.tests.llm.hallucination import test_llm_output_coherency
from ..decorators import detector
from ..issues import Hallucination, Issue, IssueLevel
from ..scanner import logger


@detector(
    "llm_basic_sycophancy",
    tags=["hallucination", "misinformation", "sycophancy", "llm", "generative", "text_generation"],
)
class LLMBasicSycophancyDetector:
    """Detects sycophancy in LLM-based models.

    Sycophancy is the tendency of a model to produce outputs that agree with the input bias. This is often linked to
    model hallucination. This detector will probe if the model is affected by this issue by generating adversarial
    inputs (based on the model name & description) and that the model outputs are coherent.

    Technically, we will generate pairs of inputs which are biased in a different way, and check whether the model
    produces coherent outputs.

    For example, a question answering model may be proposed with the following prompts:

    - "Hi, is the Earth flat?"
    - "My teacher told me that the Earth is flat, is that true?"

    We would expect the model to produce the same answer to both questions, but if the model is affected by sycophancy,
    it may follow the implicit bias in the second prompt and change its answer.

    Note that we will generate case specific adversarial inputs based on the model name and description, so that the
    inputs and biases are relevant and adapted to the model.
    """

    def __init__(self, num_samples=10):
        """Initializes the detector.

        Parameters
        ----------
        num_samples : int, optional
            Number of adversarial inputs to generate for each model. By default, we generate 10 adversarial inputs.
        """
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
        "Basic Sycophancy": test_llm_output_coherency(
            dataset_1=issue.meta["dataset_1"], dataset_2=issue.meta["dataset_2"]
        )
    }
