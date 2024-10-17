from typing import Optional, Sequence
import numpy as np
import pandas as pd
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..issues import Issue, IssueLevel, Robustness
from ..logger import logger
from ..registry import Detector


class BaseNumericalPerturbationDetector:
    """Base class for metamorphic detectors based on numerical feature perturbations."""

    _issue_group = Robustness

    def __init__(
        self,
        perturbation_fraction: float = 0.01,
        threshold: Optional[float] = None,
        num_samples: Optional[int] = None,
        output_sensitivity: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        perturbation_fraction: float
            Fractional perturbation to apply to numerical features (default is 1% change).
        threshold: Optional[float]
            The threshold for the fail rate, defined as the proportion of samples for which the model
            prediction has changed. If the fail rate is greater than the threshold, an issue is created.
        num_samples: Optional[int]
            The maximum number of samples to use for testing. If not provided, a default number is used.
        output_sensitivity: Optional[float]
            For regression models, the maximum relative change in prediction considered acceptable.
        """
        self.perturbation_fraction = perturbation_fraction
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

    def run(self, model: BaseModel, dataset: Dataset, features: Sequence[str]) -> Sequence[Issue]:
        """Run the numerical perturbation detector."""
        numerical_features = [f for f in features if pd.api.types.is_numeric_dtype(dataset.df[f])]

        logger.info(
            "%s: Running numerical perturbation detector with threshold=%.3f, "
            "perturbation_fraction=%.3f, output_sensitivity=%.3f, num_samples=%d"
            % (
                self.__class__.__name__,
                self.threshold or -1,
                self.perturbation_fraction,
                self.output_sensitivity or -1,
                self.num_samples or -1
            )
        )

        issues = []  # Initialize issues list
        for feature in numerical_features:
            issues.extend(self._detect_issues(model, dataset, feature))

        return [i for i in issues if i is not None]

    def _detect_issues(
        self,
        model: BaseModel,
        dataset: Dataset,
        feature: str,
    ) -> Sequence[Issue]:
        num_samples = self.num_samples or min(1000, len(dataset.df))
        output_sensitivity = self.output_sensitivity or 0.05
        threshold = self.threshold or 0.05

        # Generate perturbed dataset by adding a small percentage of change
        perturbation = dataset.df[feature] * self.perturbation_fraction
        perturbed_data = dataset.df.copy()
        perturbed_data[feature] += perturbation

        # Subset the dataset for faster calculations
        perturbed_data = perturbed_data.sample(n=num_samples, random_state=42)
        original_data = dataset.df.loc[perturbed_data.index]

        # Ensure column types are passed correctly as a dictionary
        original_pred = model.predict(
            Dataset(df=original_data, target=dataset.target, column_types=dict(dataset.column_types))
        )
        perturbed_pred = model.predict(
            Dataset(df=perturbed_data, target=dataset.target, column_types=dict(dataset.column_types))
        )

        # Check model type and calculate pass/fail rate
        if model.is_classification:
            passed = original_pred.raw_prediction == perturbed_pred.raw_prediction
        elif model.is_regression:
            rel_delta = np.abs((perturbed_pred.raw_prediction - original_pred.raw_prediction) / original_pred.raw_prediction)
            passed = rel_delta < output_sensitivity
        else:
            raise NotImplementedError("Only classification and regression models are supported.")

        pass_rate = passed.mean()
        fail_rate = 1 - pass_rate

        logger.info("Testing `%s` perturbation\tFail rate: %.3f" % (feature, fail_rate))

        issues = []
        if fail_rate >= threshold:
            # Severity
            issue_level = IssueLevel.MAJOR if fail_rate >= 2 * threshold else IssueLevel.MEDIUM

            # Issue description
            desc = (
                "When the feature `%s` is perturbed by %.2f%%, the model changes its prediction in %.2f%% of cases."
                % (feature, self.perturbation_fraction * 100, fail_rate * 100)
            )

            failed_size = (~passed).sum()
            slice_size = len(passed)

            issue = Issue(
                model,
                dataset,
                group=self._issue_group,
                level=issue_level,
                description=desc,
                features=[feature],
                meta={
                    "feature": feature,
                    "perturbation_fraction": self.perturbation_fraction,
                    "fail_rate": fail_rate,
                    "failed_size": failed_size,
                    "slice_size": slice_size,
                    "threshold": threshold,
                    "output_sensitivity": output_sensitivity,
                },
                importance=fail_rate,
            )

            issues.append(issue)

        return issues
