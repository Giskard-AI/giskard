from typing import Sequence

from ...models.base import BaseModel
from ...datasets.base import Dataset
from ...ml_worker.testing.tests.metamorphic import test_metamorphic_invariance
from ..decorators import detector

from .unit_perturbation import TransformationGenerator
from .issues import RobustnessIssue, RobustnessIssueInfo


@detector(name="robustness", tags=["robustness", "classification", "regression"])
class RobustnessDetector:
    def run(self, model: BaseModel, dataset: Dataset):
        if model is None:
            raise ValueError("You need to provide a model to test.")
        if dataset is None:
            raise ValueError("You need to provide an evaluation dataset.")

        # Create issues from the slices
        issues = self._detect_issues(model=model, dataset=dataset)
        return issues

    def _detect_issues(self, model: BaseModel, dataset: Dataset) -> Sequence[RobustnessIssue]:
        # Now we calculate the metric on each slice and compare it to the reference
        issues = []
        transformation = TransformationGenerator(model=model, dataset=dataset)
        for feature, feature_type in dataset.column_types.items():
            if feature_type == "numeric":
                metric_name = "Value perturbation (±2 std)"
                transformation_function = transformation.generate_std_transformation(feature)
                robustness_test = test_metamorphic_invariance(
                    model=model, dataset=dataset, transformation_function=transformation_function, threshold=0.999
                )
            elif feature_type == "text":
                metric_name = "Text perturbation"
                transformation_function = transformation.text_transformation(feature)
                robustness_test = test_metamorphic_invariance(
                    model=model, dataset=dataset, transformation_function=transformation_function, threshold=0.999
                )
            else:
                continue

            test_result = robustness_test.execute()

            if not test_result.passed:
                issue_info = RobustnessIssueInfo(
                    feature=feature,
                    metric=metric_name,
                    variation_ratio=1 - test_result.metric,
                    messages=test_result.messages,
                )

                issue = RobustnessIssue(model=model, dataset=dataset, level="medium", info=issue_info)
                issues.append(issue)

        return issues
