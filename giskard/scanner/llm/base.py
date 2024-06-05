from typing import Sequence

import pandas as pd

from ...datasets.base import Dataset
from ...llm.evaluators import RequirementEvaluator
from ...llm.evaluators.base import EvaluationResult
from ...llm.generators import AdversarialDataGenerator
from ...llm.testcase import TestcaseRequirementsGenerator
from ...llm.utils import format_chat_messages
from ...models.base.model import BaseModel
from ...testing.tests.llm import test_llm_output_against_requirement
from ..issues import Issue
from ..registry import Detector
from ..scanner import logger


class RequirementBasedDetector(Detector):
    _taxonomy = []

    def __init__(self, num_requirements=4, num_samples=5, llm_seed: int = 1729):
        self.num_requirements = num_requirements
        self.num_samples = num_samples
        self.llm_seed = llm_seed

    def get_cost_estimate(self, model: BaseModel, dataset: Dataset) -> dict:
        counts = _estimate_base_token_counts(model, dataset)
        model_meta_tokens = counts["model_meta_tokens"]
        input_sample_tokens = counts["input_sample_tokens"]

        num_calls = 0
        num_prompt_tokens = 0
        num_sampled_tokens = 0

        # Requirement generation: base prompt + model meta
        num_calls += 1
        num_prompt_tokens += 320 + model_meta_tokens  # base prompt is roughly 320 tokens long
        num_sampled_tokens += 30 * self.num_requirements  # generated requirements are typically 30 tokens long

        # Adversarial examples generation, for each generated requirement
        num_calls += self.num_requirements
        num_prompt_tokens += self.num_requirements * (500 + model_meta_tokens + len(self.get_issue_description()) // 4)
        num_sampled_tokens += self.num_requirements * input_sample_tokens * self.num_samples

        # Evaluation of adversarial examples, for each example
        num_calls += self.num_requirements * self.num_samples
        # base prompt: 200, requirement: 30, model output: 50
        num_prompt_tokens += (
            self.num_requirements * self.num_samples * (200 + model_meta_tokens + input_sample_tokens + 30 + 50)
        )
        num_sampled_tokens += self.num_requirements * self.num_samples * 15

        return {
            "model_predict_calls": self.num_requirements * self.num_samples,
            "llm_calls": num_calls,
            "llm_prompt_tokens": num_prompt_tokens,
            "llm_sampled_tokens": num_sampled_tokens,
        }

    def run(self, model: BaseModel, dataset: Dataset, features=None) -> Sequence[Issue]:
        issue_description = self.get_issue_description()

        logger.info(f"{self.__class__.__name__}: Generating test case requirements")
        requirements_gen = TestcaseRequirementsGenerator(issue_description)
        requirements = requirements_gen.generate_requirements(model, self.num_requirements)

        logger.info(f"{self.__class__.__name__}: Evaluating test cases")
        issues = []
        for requirement in requirements:
            logger.info(f"{self.__class__.__name__}: Evaluating requirement: {requirement}")

            languages = dataset.extract_languages(columns=model.meta.feature_names)

            dg = AdversarialDataGenerator(
                issue_description=issue_description, requirement=requirement, languages=languages
            )
            eval_dataset = dg.generate_dataset(model, self.num_samples)

            evaluator = RequirementEvaluator([requirement])
            eval_result = evaluator.evaluate(model, eval_dataset)

            if eval_result.failed:
                issues.append(self.make_issue(model, eval_dataset, requirement, eval_result))
                logger.info(
                    f"{self.__class__.__name__}: Test case failed ({len(eval_result.failure_examples)} failed examples)"
                )
            else:
                logger.info(f"{self.__class__.__name__}: Test case passed")

        return issues

    def make_issue(self, model: BaseModel, dataset: Dataset, requirement: str, eval_result: EvaluationResult) -> Issue:
        examples = pd.DataFrame(
            [
                {
                    "Conversation": format_chat_messages(ex["sample"].get("conversation", [])),
                    "Reason": ex.get("reason", "No reason provided."),
                }
                for ex in eval_result.failure_examples
            ]
        )

        return Issue(
            model,
            dataset,
            group=self._issue_group,
            level=self._issue_level,
            description="The model does not satisfy the following requirement: " + requirement,
            examples=examples,
            meta={
                "metric": "Failing samples",
                "metric_value": len(examples),
                "domain": requirement,
                "requirement": requirement,
                "deviation": f"Found {len(examples)} model output{'s' if len(examples) > 1 else ''} not meeting the requirement",
                "hide_index": True,
            },
            tests=_generate_output_requirement_tests,
            taxonomy=self._taxonomy,
            detector_name=self.__class__.__name__,
        )


def _generate_output_requirement_tests(issue: Issue):
    return {
        issue.meta["requirement"]: test_llm_output_against_requirement(
            dataset=issue.dataset, requirement=issue.meta["requirement"]
        )
    }


def _estimate_base_token_counts(model: BaseModel, dataset: Dataset) -> int:
    # Note: For OpenAI (GPT-4), a token generally correspond to ~4 characters for English text.
    # We use this rule of thumb to give a rough estimate of the number of tokens in a prompt.
    model_meta_tokens = (
        len(model.meta.name) + len(model.meta.description) + len(",".join(model.meta.feature_names))
    ) // 4

    if len(dataset) > 3:
        input_sample_tokens = (
            sum(dataset.df[f].apply(lambda x: len(str(x))).mean() for f in model.meta.feature_names) // 4
        )
    else:
        input_sample_tokens = 30

    return {"model_meta_tokens": model_meta_tokens, "input_sample_tokens": input_sample_tokens}
