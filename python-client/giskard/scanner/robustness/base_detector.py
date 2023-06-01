import numpy as np
from typing import Sequence

from ..issues import Issue
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ...scanner.registry import Detector
from .issues import RobustnessIssue, RobustnessIssueInfo
from ...ml_worker.testing.registry.transformation_function import TransformationFunction


class TextPerturbationDetector(Detector):
    transformation: TransformationFunction

    def __init__(self, threshold: float = 0.90, output_sensitivity=0.1, num_samples: int = 1_000):
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        features = [col for col, col_type in dataset.column_types.items() if col_type == "text"]

        issues = []
        for feature in features:
            issue = self._maybe_detect_issue(model, dataset, feature)
            if issue:
                issues.append(issue)

        return issues

    def _maybe_detect_issue(self, model: BaseModel, dataset: Dataset, feature: str):
        transformation_fn = self.transformation(column=feature)
        transformed = dataset.select_columns([feature]).transform(transformation_fn)

        # Select only the records which were changed
        changed_idx = dataset.df.index[transformed.df[feature] != dataset.df[feature]]

        # Select a random subset of the changed records
        if len(changed_idx) > self.num_samples:
            rng = np.random.default_rng(747)
            changed_idx = changed_idx[rng.choice(len(changed_idx), self.num_samples)]

        original_data = Dataset(dataset.df.loc[changed_idx], target=dataset.target, column_types=dataset.column_types)
        perturbed_data = Dataset(
            transformed.df.loc[changed_idx], target=dataset.target, column_types=dataset.column_types
        )

        # Calculate predictions
        original_pred = model.predict(original_data)
        perturbed_pred = model.predict(perturbed_data)

        if model.is_classification:
            passed = np.isclose(original_pred.raw_prediction, perturbed_pred.raw_prediction)
        elif model.is_regression:
            rel_delta = _relative_delta(perturbed_pred.raw_prediction, original_pred.raw_prediction)
            passed = np.abs(rel_delta) < self.output_sensitivity
        else:
            raise NotImplementedError("Only classification and regression models are supported.")

        pass_ratio = passed.mean()
        fail_ratio = 1 - pass_ratio

        if pass_ratio < self.threshold:
            info = RobustnessIssueInfo(
                feature=feature,
                fail_ratio=fail_ratio,
                perturbation_name=getattr(self.transformation, "name", self.transformation.meta.name),
            )
            return RobustnessIssue(
                model,
                dataset,
                level="major" if pass_ratio < 0.5 * self.threshold else "medium",
                info=info,
            )


def _relative_delta(actual, reference):
    return (actual - reference) / reference
