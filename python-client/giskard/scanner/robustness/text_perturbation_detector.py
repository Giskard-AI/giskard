import numpy as np
import pandas as pd
from typing import Sequence, Optional

from .text_transformations import TextTransformation
from ..issues import Issue
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..registry import Detector
from .issues import RobustnessIssue, RobustnessIssueInfo
from ..decorators import detector
from ..logger import logger


@detector(name="text_perturbation", tags=["text_perturbation", "robustness", "nlp", "classification", "regression"])
class TextPerturbationDetector(Detector):
    def __init__(
        self,
        transformations: Optional[Sequence[TextTransformation]] = None,
        threshold: float = 0.05,
        output_sensitivity=0.05,
        num_samples: int = 1_000,
    ):
        self.transformations = transformations
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        transformations = self.transformations or self._get_default_transformations(model, dataset)
        features = [col for col, col_type in dataset.column_types.items() if col_type == "text"]

        # Also check that the text column is string
        # @TODO: fix thix in the dataset internals
        features = [col for col in features if pd.api.types.is_string_dtype(dataset.df[col].dtype)]

        logger.debug(
            f"TextPerturbationDetector: Running with transformations={[t.name for t in transformations]} "
            f"threshold={self.threshold} output_sensitivity={self.output_sensitivity} num_samples={self.num_samples}"
        )

        issues = []
        for transformation in transformations:
            issues.extend(self._detect_issues(model, dataset, transformation, features))

        return [i for i in issues if i is not None]

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            TextUppercase,
            TextLowercase,
            TextTitleCase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
            TextGenderTransformation,
        )

        return [
            TextUppercase,
            TextLowercase,
            TextTitleCase,
            TextTypoTransformation,
            TextPunctuationRemovalTransformation,
            TextGenderTransformation,
        ]

    def _detect_issues(
        self,
        model: BaseModel,
        dataset: Dataset,
        transformation: TextTransformation,
        features: Sequence[str],
    ) -> Sequence[Issue]:
        issues = []
        # @TODO: integrate this with Giskard metamorphic tests already present
        for feature in features:
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
                passed = original_pred.raw_prediction == perturbed_pred.raw_prediction
            elif model.is_regression:
                rel_delta = _relative_delta(perturbed_pred.raw_prediction, original_pred.raw_prediction)
                passed = np.abs(rel_delta) < self.output_sensitivity
            else:
                raise NotImplementedError("Only classification and regression models are supported.")

            pass_ratio = passed.mean()
            fail_ratio = 1 - pass_ratio

            logger.debug(
                f"TextPerturbationDetector: Testing `{feature}` for perturbation `{transformation.name}`\tFail rate: {fail_ratio:.3f}"
            )

            if fail_ratio >= self.threshold:
                info = RobustnessIssueInfo(
                    feature=feature,
                    fail_ratio=fail_ratio,
                    transformation_fn=transformation_fn,
                    perturbed_data_slice=perturbed_data,
                    perturbed_data_slice_predictions=perturbed_pred,
                    fail_data_idx=original_data.df[~passed].index.values,
                    threshold=self.threshold,
                    output_sensitivity=self.output_sensitivity,
                )
                issue = RobustnessIssue(
                    model,
                    dataset,
                    level="major" if fail_ratio >= 2 * self.threshold else "medium",
                    info=info,
                )
                issues.append(issue)

        return issues


def _relative_delta(actual, reference):
    return (actual - reference) / reference
