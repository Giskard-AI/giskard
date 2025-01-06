from typing import Optional, Sequence

import numpy as np

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..issues import Issue, IssueLevel, Robustness
from ..logger import logger
from .numerical_transformations import NumericalTransformation


class BaseNumericalPerturbationDetector:
    """Base class for metamorphic detectors based on numerical feature perturbations."""

    _issue_group = Robustness

    def __init__(
        self,
        transformations: Optional[Sequence[NumericalTransformation]] = None,
        threshold: Optional[float] = None,
        num_samples: Optional[int] = None,
        output_sensitivity: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        transformations: Optional[Sequence[NumericalTransformation]]
            The numerical transformations used in the metamorphic testing. If not provided, a default set of transformations will be used.
        threshold: Optional[float]
            The threshold for the fail rate, defined as the proportion of samples for which the model
            prediction has changed. If the fail rate is greater than the threshold, an issue is created.
        num_samples: Optional[int]
            The maximum number of samples to use for testing. If not provided, a default number is used.
        output_sensitivity: Optional[float]
            For regression models, the maximum relative change in prediction considered acceptable.
        """
        self.transformations = transformations
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

    def run(self, model: BaseModel, dataset: Dataset, features: Sequence[str]) -> Sequence[Issue]:
        transformations = self.transformations or self._get_default_transformations(model, dataset)
        if transformations is None:
            raise ValueError("Transformations should not be None")
        # Only analyze numerical features
        numerical_features = [f for f in features if dataset.column_types[f] == "numeric"]

        logger.info(
            f"{self.__class__.__name__}: Running with transformations={[t.name for t in transformations]} "
            f"threshold={self.threshold} output_sensitivity={self.output_sensitivity} num_samples={self.num_samples}"
        )

        issues = []
        for transformation in transformations:
            issues.extend(self._detect_issues(model, dataset, transformation, numerical_features))

        return [i for i in issues if i is not None]

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[NumericalTransformation]:
        ...

    def _detect_issues(
        self,
        model: BaseModel,
        dataset: Dataset,
        transformation: NumericalTransformation,
        features: Sequence[str],
    ) -> Sequence[Issue]:
        num_samples = self.num_samples or min(1000, len(dataset.df))
        output_sensitivity = self.output_sensitivity or 0.05
        threshold = self.threshold or 0.05

        issues = []
        for feature in features:
            transformation_fn = transformation(column=feature)
            transformed = dataset.transform(transformation_fn)

            # Select only the records which were changed
            changed_idx = dataset.df.index[transformed.df[feature] != dataset.df[feature]]

            if changed_idx.empty:
                continue

            # Select a random subset of the changed records
            if len(changed_idx) > num_samples:
                rng = np.random.default_rng(747)
                changed_idx = changed_idx[rng.choice(len(changed_idx), num_samples, replace=False)]

            original_data = Dataset(
                dataset.df.loc[changed_idx],
                target=dataset.target,
                column_types=dataset.column_types,
                validation=False,
            )
            perturbed_data = Dataset(
                transformed.df.loc[changed_idx],
                target=dataset.target,
                column_types=dataset.column_types,
                validation=False,
            )
            # Ensure column types are passed correctly as a dictionary
            original_pred = model.predict(original_data)
            perturbed_pred = model.predict(perturbed_data)

            # Check model type and calculate pass/fail rate
            if model.is_classification:
                passed = original_pred.raw_prediction == perturbed_pred.raw_prediction
            elif model.is_regression:
                rel_delta = np.abs(
                    (perturbed_pred.raw_prediction - original_pred.raw_prediction) / original_pred.raw_prediction
                )
                passed = rel_delta < output_sensitivity
            else:
                raise NotImplementedError("Only classification and regression models are supported.")

            pass_rate = passed.mean()
            fail_rate = 1 - pass_rate

            logger.info(
                f"{self.__class__.__name__}: Testing `{feature}` for perturbation `{transformation.name}`\tFail rate: {fail_rate:.3f}"
            )

            issues = []
            if fail_rate >= threshold:
                # Severity
                issue_level = IssueLevel.MAJOR if fail_rate >= 2 * threshold else IssueLevel.MEDIUM

                # Issue description
                desc = (
                    "When feature “{feature}” is perturbed with the transformation “{transformation_fn}”, "
                    "the model changes its prediction in {fail_rate_percent}% of the cases. "
                    "We expected the predictions not to be affected by this transformation."
                )

                failed_size = (~passed).sum()
                slice_size = len(passed)
                # Determine the transformation function name
                transformation_fn_name = transformation_fn.name
                issue = Issue(
                    model,
                    dataset,
                    group=self._issue_group,
                    level=issue_level,
                    description=desc,
                    features=[feature],
                    transformation_fn=transformation_fn_name,
                    meta={
                        "feature": feature,
                        "domain": f"Feature `{feature}`",
                        "deviation": f"{failed_size}/{slice_size} tested samples ({round(fail_rate * 100, 2)}%) changed prediction after perturbation",
                        "fail_rate": fail_rate,
                        "failed_size": failed_size,
                        "slice_size": slice_size,
                        "threshold": threshold,
                        "output_sensitivity": output_sensitivity,
                        "metric": "Fail rate",
                        "metric_value": fail_rate,
                    },
                    importance=fail_rate,
                )

                issues.append(issue)

        return issues
