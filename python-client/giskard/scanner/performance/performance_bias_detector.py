import scipy
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


@detector(name="performance_bias", tags=["performance_bias", "performance", "classification", "regression"])
class PerformanceBiasDetector(LossBasedDetector):
    def __init__(
        self,
        metrics: Optional[Sequence] = None,
        loss: Union[Optional[str], Callable[[BaseModel, Dataset], np.ndarray]] = None,
        threshold: float = 0.05,
        alpha: Optional[float] = None,
        method: str = "tree",
    ):
        """Performance bias detector.

        Parameters
        ----------
        metrics : Sequence, optional
            List of metrics to use for the bias detection. If not provided, the default metrics for the model type
            will be used. Available metrics are: `accuracy`, `balanced_accuracy`, `auc`, `f1`, `precision`, `recall`,
            `mse`, `mae`.
        loss : str or callable, optional
            Loss function to use for the slice search. If not provided, will use `log_loss` for classification models
            and `mse` for regression models.
        threshold : float, optional
            Threshold for the deviation of metrics between slices and the overall dataset. If the deviation is larger
            than the threshold, an issue will be reported.
        alpha : float, optional
            Experimental: false discovery rate for issue detection. If a value is provided, false discovery rate will be
            controlled with a Benjamini–Hochberg procedure, and only statistically significant issues will be reported.
            This is disabled by default because only a subset of metrics are currently supported.
        method : str, optional
            The slicing method used to find the data slices. Available methods are: `tree`, `bruteforce`, `optimal`,
            `multiscale`. Default is `tree`.
        """
        self.metrics = metrics
        self.threshold = threshold
        self.method = method
        self.alpha = alpha
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
        self, slices: Sequence[SlicingFunction], model: BaseModel, dataset: Dataset, meta: pd.DataFrame
    ) -> Sequence[PerformanceIssue]:
        # Use a precooked model to speed up the tests
        precooked = PrecookedModel.from_model(model, dataset)
        detector = IssueFinder(self.metrics, self.threshold, self.alpha)
        issues = detector.detect(precooked, dataset, slices)

        # Restore the original model
        for issue in issues:
            issue.model = model

        return issues


class IssueFinder:
    def __init__(self, metrics: Optional[Sequence] = None, threshold: float = 0.1, alpha: Optional[float] = 0.10):
        self.metrics = metrics
        self.threshold = threshold
        self.alpha = alpha

    def detect(self, model: BaseModel, dataset: Dataset, slices: Sequence[SlicingFunction]):
        logger.info(f"PerformanceBiasDetector: Testing {len(slices)} slices for performance issues.")

        # Prepare metrics
        metrics = self._get_default_metrics(model, dataset) if self.metrics is None else self.metrics
        metrics = [get_metric(m) for m in metrics]

        issues = []
        p_values = []

        for metric in metrics:
            issues_, p_values_ = self._detect_for_metric(model, dataset, slices, metric)
            issues.extend(issues_)
            p_values.extend(p_values_)

        # EXPERIMENTAL: Benjamini–Hochberg procedure to control false detection rate.
        if self.alpha is not None:
            p_values = np.array(p_values)
            p_values_rank = p_values.argsort() + 1
            p_value_threshold = p_values[p_values <= p_values_rank / len(p_values) * self.alpha].max()
            logger.info(f"PerformanceBiasDetector: Benjamini–Hocheberg p-value threshold is {p_value_threshold:.3e}")
            issues = [issue for issue in issues if issue.info.p_value <= p_value_threshold]
            logger.info(f"PerformanceBiasDetector: Kept {len(issues)} significant issues out of {len(p_values)}.")

        # Group issues by slice and keep only the most critical
        issues_by_slice = defaultdict(list)
        for issue in issues:
            issues_by_slice[issue.info.slice_fn].append(issue)

        return sorted(
            [max(group, key=lambda i: i.importance) for group in issues_by_slice.values()], key=lambda i: i.importance
        )

    def _get_default_metrics(self, model: BaseModel, dataset: Dataset):
        if model.is_classification:
            metrics = ["precision", "recall"]
            metrics.append("balanced_accuracy" if _is_unbalanced_target(dataset.df[dataset.target]) else "accuracy")
            return metrics

        return ["mse", "mae"]

    def _detect_for_metric(
        self,
        model: BaseModel,
        dataset: Dataset,
        slices: Sequence[SlicingFunction],
        metric: PerformanceMetric,
    ):
        # Calculate the metric on the reference dataset
        ref_metric = metric(model, dataset)

        # Now we calculate the metric on each slice and compare it to the reference
        issues = []
        p_values = []
        compute_pvalue = self.alpha is not None
        for slice_fn in slices:
            sliced_dataset, slice_metric, p_value = _calculate_slice_metrics(
                model, dataset, metric, slice_fn, with_pvalue=compute_pvalue
            )

            # If we do not have enough samples, skip the slice
            if not compute_pvalue and slice_metric.affected_samples < 20:
                logger.info(
                    f"PerformanceBiasDetector: Skipping slice {slice_fn} because metric was estimated on < 20 samples."
                )
                continue

            # If the p-value could not be estimated, skip the slice
            if compute_pvalue and p_value is not None and np.isnan(p_value):
                logger.info(
                    f"PerformanceBiasDetector: Skipping slice {slice_fn} since the p-value could not be estimated."
                )
                continue

            p_values.append(p_value)

            # Calculate the relative delta
            relative_delta = (slice_metric.value - ref_metric.value) / ref_metric.value

            if metric.greater_is_better:
                is_issue = relative_delta < -self.threshold
            else:
                is_issue = relative_delta > self.threshold

            logger.info(
                f"PerformanceBiasDetector: Testing slice {slice_fn}\t{metric.name} = {slice_metric.value:.3f} "
                f"(global {ref_metric.value:.3f}) Δm = {relative_delta:.3f}"
                f"\tis_issue = {is_issue}"
            )

            if is_issue:
                level = "major" if abs(relative_delta) > 2 * self.threshold else "medium"

                issue_info = PerformanceIssueInfo(
                    slice_fn=slice_fn,
                    metric=metric,
                    metric_value_slice=slice_metric.value,
                    metric_value_reference=ref_metric.value,
                    slice_size=len(sliced_dataset),
                    threshold=self.threshold,
                    p_value=p_value,
                )

                issues.append(PerformanceIssue(model, dataset, level=level, info=issue_info))

        return issues, p_values


def _is_unbalanced_target(classes: pd.Series):
    return (classes.value_counts() / classes.count()).std() > 0.2


def _calculate_slice_metrics(model, dataset, metric, slice_fn, with_pvalue=False):
    sliced_dataset = dataset.slice(slice_fn)
    slice_metric = metric(model, sliced_dataset)

    if not with_pvalue:
        return sliced_dataset, slice_metric, None

    # Perform statistical tests
    complementary_dataset = dataset.slice(lambda df: df[~df.index.isin(sliced_dataset.df.index)], row_level=False)
    comp_metric = metric(model, complementary_dataset)

    try:
        # If we have raw values for the metric, we perform a standard t-test
        if slice_metric.raw_values is not None:
            alternative = "less" if metric.greater_is_better else "greater"
            _, pvalue = scipy.stats.ttest_ind(
                slice_metric.raw_values, comp_metric.raw_values, equal_var=False, alternative=alternative
            )
        else:
            # otherwise, this must be classification scores, so we perform a G-test
            slice_x_cnt = round(slice_metric.value * slice_metric.affected_samples)
            slice_y_cnt = slice_metric.affected_samples - slice_x_cnt

            comp_x_cnt = round(comp_metric.value * comp_metric.affected_samples)
            comp_y_cnt = comp_metric.affected_samples - comp_x_cnt

            ctable = [[slice_x_cnt, slice_y_cnt], [comp_x_cnt, comp_y_cnt]]

            pvalue = scipy.stats.chi2_contingency(ctable, lambda_="log-likelihood")[1]
    except ValueError:
        pvalue = np.nan

    return sliced_dataset, slice_metric, pvalue
