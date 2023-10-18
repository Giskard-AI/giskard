from abc import abstractmethod
from typing import Sequence

import pandas as pd

from ..scanner import logger
from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..issues import Issue, IssueGroup
from .testcase import RequirementDataGenerator, RequirementEvaluator, RequirementsGenerator


class RequirementBasedDetector:
    def __init__(self, num_requirements=5, num_samples=3):
        self.num_requirements = num_requirements
        self.num_samples = num_samples

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        issue_description = self.get_issue_description()

        logger.info(f"{self.__class__.__name__}: Generating test case requirements")
        requirements_gen = RequirementsGenerator(issue_description)
        requirements = requirements_gen.generate_requirements(model, self.num_requirements)

        evaluator = RequirementEvaluator(requirements)

        logger.info(f"{self.__class__.__name__}: Evaluating test cases")
        issues = []
        for requirement in requirements:
            logger.info(f"{self.__class__.__name__}: Evaluating requirement: {requirement}")
            dg = RequirementDataGenerator(issue_description=issue_description, requirement=requirement)
            eval_dataset = dg.generate_dataset(model, self.num_samples)
            eval_result = evaluator.evaluate(model, eval_dataset)

            if eval_result.failed:
                issues.append(
                    self.make_issue(
                        model, eval_dataset, requirement, requirements, pd.DataFrame(eval_result.failure_examples)
                    )
                )
                logger.info(
                    f"{self.__class__.__name__}: Test case failed ({len(eval_result.failure_examples)} failed examples)"
                )
            else:
                logger.info(f"{self.__class__.__name__}: Test case passed")

        return issues

    @abstractmethod
    def get_issue_description(self) -> str:
        ...

    def make_issue(
        self, model: BaseModel, dataset: Dataset, requirement: str, requirements: Sequence[str], examples: pd.DataFrame
    ) -> IssueGroup:
        from ...testing.tests.llm import test_llm_output_requirement

        return Issue(
            model,
            dataset,
            group=self._issue_group,
            level=self._issue_level,
            description="The model does not satisfy the following requirement: " + requirement,
            examples=examples,
            meta={
                "domain": requirement,
                "deviation": f"{len(examples)} failing sample{'s' if len(examples) > 1 else ''} found",
                "hide_index": True,
            },
            tests={
                requirement: test_llm_output_requirement(
                    model=model, dataset=dataset, requirements="\n- ".join(requirements)
                )
            },
        )
