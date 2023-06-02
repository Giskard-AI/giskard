import numpy as np
import pandas as pd
from sklearn import metrics
from collections import defaultdict
from typing import Callable, Optional, Sequence, Union

from ..common.loss_based_detector import LossBasedDetector
from ...models.base import BaseModel
from ...models._precooked import PrecookedModel
from ...datasets.base import Dataset
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from .issues import PerformanceIssue, PerformanceIssueInfo
from .metrics import PerformanceMetric, get_metric
from ..decorators import detector
from ..logger import logger
from ...client.python_utils import warning


@detector(name="performance_bias", tags=["performance_bias", "classification", "regression"])
class PerformanceBiasDetector(LossBasedDetector):
    def __init__(
        self,
        metrics: Optional[Sequence] = None,
        loss: Union[Optional[str], Callable[[BaseModel, Dataset], np.ndarray]] = None,
        threshold: float = 0.05,
        method: str = "tree",
    ):
        self.metrics = metrics
        self.threshold = threshold
        self.method = method
        self.loss = loss

    @property
    def _numerical_slicer_method(self):
        return self.method

    def _calculate_loss(self, model, dataset):
        true_target = dataset.df.loc[:, dataset.target].values
        pred = model.predict(dataset)

        loss = self.loss
        if loss is None:
            loss = "log_loss" if model.is_classification else "mse"

        if callable(loss):
            try:
                loss_values = loss(model, dataset)
            except Exception as err:
                raise RuntimeError("The provided loss function returned an error.") from err
        else:
            # Validate string loss function
            if loss not in ["log_loss", "mse", "mae"]:
                invalid_loss = loss
                loss = "log_loss" if model.is_classification == "classification" else "mse"
                warning(f"PerformanceBiasDetector: Unknown loss function `{invalid_loss}`. Using `{loss}` instead.")

            if loss == "log_loss":
                loss_values = [
                    metrics.log_loss([true_label], [probs], labels=model.meta.classification_labels)
                    for true_label, probs in zip(true_target, pred.raw)
                ]
            elif loss == "mse":
                loss_values = [
                    metrics.mean_squared_error([y_true], [y_pred]) for y_true, y_pred in zip(true_target, pred.raw)
                ]
            elif loss == "mae":
                loss_values = [
                    metrics.mean_absolute_error([y_true], [y_pred]) for y_true, y_pred in zip(true_target, pred.raw)
                ]
            else:
                raise ValueError(f"Invalid loss function `{loss}`.")

        return pd.DataFrame({"__gsk__loss": loss_values}, index=dataset.df.index)

    def _find_issues(
        self,
        slices: Sequence[SlicingFunction],
        model: BaseModel,
        dataset: Dataset,
        meta: pd.DataFrame,
    ) -> Sequence[PerformanceIssue]:
        # Use a precooked model to speed up the tests
        precooked = PrecookedModel.from_model(model, dataset)
        detector = IssueFinder(self.metrics, self.threshold)
        issues = detector.detect(precooked, dataset, slices)

        # Restore the original model
        for issue in issues:
            issue.model = model

        return issues


class IssueFinder:
    def __init__(self, metrics: Optional[Sequence] = None, threshold: float = 0.1):
        self.metrics = metrics
        self.threshold = threshold

    def detect(self, model: BaseModel, dataset: Dataset, slices: Sequence[SlicingFunction]):
        logger.info(f"PerformanceBiasDetector: Testing {len(slices)} slices for performance issues.")

        # Prepare metrics
        metrics = self._get_default_metrics(model, dataset) if self.metrics is None else self.metrics
        metrics = [get_metric(m) for m in metrics]

        issues = []

        for metric in metrics:
            issues.extend(self._detect_for_metric(model, dataset, slices, metric))

        # Group issues by slice and keep only the most critical
        issues_by_slice = defaultdict(list)
        for issue in issues:
            issues_by_slice[issue.info.slice_fn].append(issue)

        return sorted(
            [max(group, key=lambda i: i.importance) for group in issues_by_slice.values()], key=lambda i: i.importance
        )

    def _get_default_metrics(self, model: BaseModel, dataset: Dataset):
        if model.is_classification:
            metrics = ["f1", "precision", "recall"]
            metrics.append("balanced_accuracy" if _is_unbalanced_target(dataset.df[dataset.target]) else "accuracy")
            return metrics

        return ["mse", "mae"]

    def _detect_for_metric(
        self, model: BaseModel, dataset: Dataset, slices: Sequence[SlicingFunction], metric: PerformanceMetric
    ):
        # Calculate the metric on the reference dataset
        ref_metric_val = metric(model, dataset)

        # Now we calculate the metric on each slice and compare it to the reference
        issues = []
        for slice_fn in slices:
            sliced_dataset = dataset.slice(slice_fn)
            metric_val = metric(model, sliced_dataset)
            relative_delta = (metric_val - ref_metric_val) / ref_metric_val

            if metric.greater_is_better:
                is_issue = relative_delta < -self.threshold
            else:
                is_issue = relative_delta > self.threshold

            logger.info(
                f"PerformanceBiasDetector: Testing slice {slice_fn}\t{metric.name} = {metric_val:.3f} (global {ref_metric_val:.3f}) Δm = {relative_delta:.3f}\tis_issue = {is_issue}"
            )

            if is_issue:
                level = "major" if abs(relative_delta) > 2 * self.threshold else "medium"

                issue_info = PerformanceIssueInfo(
                    slice_fn=slice_fn,
                    metric=metric,
                    metric_value_slice=metric_val,
                    metric_value_reference=ref_metric_val,
                    slice_size=len(sliced_dataset),
                    threshold=self.threshold,
                )

                issues.append(
                    PerformanceIssue(
                        model,
                        dataset,
                        level=level,
                        info=issue_info,
                    )
                )

        return issues


def _is_unbalanced_target(classes: pd.Series):
    return (classes.value_counts() / classes.count()).std() > 0.2
