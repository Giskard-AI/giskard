from typing import Optional, Sequence
from ..models.base import BaseModel
from ..datasets.base import Dataset
from giskard.scanner.unit_perturbation import TransformationGenerator
from giskard.ml_worker.testing.tests.metamorphic import test_metamorphic_invariance
from .result import ScanResult
from .robustness.issues import RobustnessIssue, RobustnessIssueInfo


class ModelRobustnessDetector:
    def __init__(self, model: Optional[BaseModel] = None, dataset: Optional[Dataset] = None):
        self.model = model
        self.dataset = dataset

    def run(self,
            model: Optional[BaseModel] = None,
            dataset: Optional[Dataset] = None):

        model = model or self.model
        dataset = dataset or self.dataset

        if model is None:
            raise ValueError("You need to provide a model to test.")
        if dataset is None:
            raise ValueError("You need to provide an evaluation dataset.")

        # Check if we have enough data to run the scan
        # if len(dataset) < 100:
        #     warning("Skipping model bias scan: the dataset is too small.")
        #     return []

        # Create issues from the slices
        issues = self._detect_issues(model=model,
                                dataset=dataset)
        return issues

    def _detect_issues(self, model: BaseModel, dataset: Dataset) -> Sequence[RobustnessIssue]:
        # Now we calculate the metric on each slice and compare it to the reference
        issues = []
        transformation = TransformationGenerator(model=model, dataset=dataset)
        for feature, feature_type in dataset.column_types.items():
            if feature_type == "numeric":
                transformation_function = transformation.generate_std_transformation(feature)

                test_result = test_metamorphic_invariance(
                    model=model,
                    dataset=dataset,
                    transformation_function=transformation_function,
                    threshold=0.999
                ).execute()

            elif feature_type == "text":
                transformation_function = transformation.text_transformation(feature)
                test_result = test_metamorphic_invariance(
                    model=model,
                    dataset=dataset,
                    transformation_function=transformation_function,
                    threshold=0.999
                ).execute()

            else:
                continue

            issue_info = RobustnessIssueInfo(
                actual_slices_size=test_result.actual_slices_size,
                metric=test_result.metric,
                passed=test_result.passed,
                messages=test_result.messages)

            issue = RobustnessIssue(
                model=model,
                dataset=dataset,
                level="??",
                info=issue_info
            )
            issues.append(issue)

        return issues
