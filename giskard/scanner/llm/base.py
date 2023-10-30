from typing import Sequence

import pandas as pd

from ...datasets.base import Dataset
from ...llm.evaluators import RequirementEvaluator
from ...llm.generators import AdversarialDataGenerator
from ...llm.testcase import TestcaseRequirementsGenerator
from ...models.base.model import BaseModel
from ...testing.tests.llm.output_requirements import test_llm_output_requirement
from ..issues import Issue
from ..scanner import logger


class RequirementBasedDetector:
    def __init__(self, num_requirements=4, num_samples=5):
        self.num_requirements = num_requirements
        self.num_samples = num_samples

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        issue_description = self.get_issue_description()

        logger.info(f"{self.__class__.__name__}: Generating test case requirements")
        requirements_gen = TestcaseRequirementsGenerator(issue_description)
        requirements = requirements_gen.generate_requirements(model, self.num_requirements)

        logger.info(f"{self.__class__.__name__}: Evaluating test cases")
        issues = []
        for requirement in requirements:
            logger.info(f"{self.__class__.__name__}: Evaluating requirement: {requirement}")
            dg = AdversarialDataGenerator(issue_description=issue_description, requirement=requirement)
            eval_dataset = dg.generate_dataset(model, self.num_samples)

            evaluator = RequirementEvaluator([requirement])
            eval_result = evaluator.evaluate(model, eval_dataset)

            if eval_result.failed:
                issues.append(
                    self.make_issue(model, eval_dataset, requirement, pd.DataFrame(eval_result.failure_examples))
                )
                logger.info(
                    f"{self.__class__.__name__}: Test case failed ({len(eval_result.failure_examples)} failed examples)"
                )
            else:
                logger.info(f"{self.__class__.__name__}: Test case passed")

        return issues

    def make_issue(self, model: BaseModel, dataset: Dataset, requirement: str, examples: pd.DataFrame) -> Issue:
        return Issue(
            model,
            dataset,
            group=self._issue_group,
            level=self._issue_level,
            description="The model does not satisfy the following requirement: " + requirement,
            examples=examples,
            meta={
                "domain": requirement,
                "requirement": requirement,
                "deviation": f"{len(examples)} failing sample{'s' if len(examples) > 1 else ''} found",
                "hide_index": True,
            },
            tests=_generate_output_requirement_tests,
        )


def _generate_output_requirement_tests(issue: Issue):
    return {
        issue.meta["requirement"]: test_llm_output_requirement(
            model=issue.model, dataset=issue.dataset, requirement=issue.meta["requirement"]
        )
    }
