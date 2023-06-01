import logging
import numpy as np
from typing import Sequence, Optional

from .text_transformations import TextTransformation

from ..issues import Issue
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..registry import Detector
from .issues import RobustnessIssue, RobustnessIssueInfo
from ..decorators import detector


@detector(name="text_perturbation", tags=["text_perturbation", "robustness", "nlp", "classification", "regression"])
class TextPerturbationDetector(Detector):
    def __init__(
        self,
        transformations: Optional[Sequence[TextTransformation]] = None,
        threshold: float = 0.90,
        output_sensitivity=0.1,
        num_samples: int = 200,
    ):
        self.transformations = transformations
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        logging.debug("Running TextPerturbationDetector")

        transformations = self.transformations or self._get_default_transformations(model, dataset)
        features = [col for col, col_type in dataset.column_types.items() if col_type == "text"]

        issues = []
        for transformation in transformations:
            issues.extend(self._detect_issues(model, dataset, transformation, features))

        return [i for i in issues if i is not None]

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            text_uppercase,
            text_lowercase,
            text_titlecase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
        )

        return [
            text_uppercase,
            text_lowercase,
            text_titlecase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
        ]

    def _detect_issues(
        self,
        model: BaseModel,
        dataset: Dataset,
        transformation: TextTransformation,
        features: Sequence[str],
    ) -> Sequence[Issue]:
        issues = []
        for feature in features:
            logging.debug(f"Running '{transformation.name}'")

            transformation_fn = transformation(column=feature)
            transformed = dataset.transform(transformation_fn)

            # Select only the records which were changed
            changed_idx = dataset.df.index[transformed.df[feature] != dataset.df[feature]]

            if changed_idx.empty:
                continue

            # Select a random subset of the changed records
            if len(changed_idx) > self.num_samples:
                rng = np.random.default_rng(747)
                changed_idx = changed_idx[rng.choice(len(changed_idx), self.num_samples)]

            original_data = Dataset(
                dataset.df.loc[changed_idx], target=dataset.target, column_types=dataset.column_types
            )
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

            logging.debug(f"Text perturbation '{transformation.name}' fail ratio: {fail_ratio:.2f}")

            if pass_ratio < self.threshold:
                info = RobustnessIssueInfo(
                    feature=feature, fail_ratio=fail_ratio, perturbation_name=getattr(transformation, "name")
                )
                issue = RobustnessIssue(
                    model,
                    dataset,
                    level="major" if pass_ratio < 0.5 * self.threshold else "medium",
                    info=info,
                )
                issues.append(issue)

        return issues


def _relative_delta(actual, reference):
    return (actual - reference) / reference
