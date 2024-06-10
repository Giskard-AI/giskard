from typing import Callable, Optional, Sequence, Union

from collections import defaultdict

import numpy as np
import pandas as pd
import scipy
from sklearn import metrics

from ...client.python_utils import warning
from ...datasets.base import Dataset
from ...models._precooked import PrecookedModel
from ...models.base import BaseModel
from ...registry.slicing_function import SlicingFunction
from ..common.examples import ExampleExtractor
from ..common.loss_based_detector import LossBasedDetector
from ..decorators import detector
from ..issues import Issue, IssueLevel, Performance
from ..logger import logger
from .metrics import PerformanceMetric, get_metric


@detector(name="performance_bias", tags=["performance_bias", "performance", "classification", "regression"])
class PerformanceBiasDetector(LossBasedDetector):
    def __init__(
        self,
        metrics: Optional[Sequence] = None,
        loss: Union[Optional[str], Callable[[BaseModel, Dataset], np.ndarray]] = None,
        threshold: float = 0.05,
        alpha: Optional[float] = None,
        method: str = "tree",
        **kwargs,
    ):
        """Performance bias detector.

        Parameters
        ----------
        metrics : Optional[Sequence]
            List of metrics to use for the bias detection. If not provided, the default metrics for the model type
            will be used. Available metrics are: `accuracy`, `balanced_accuracy`, `auc`, `f1`, `precision`, `recall`,
            `mse`, `mae`.
        loss : Optional[Union[str,callable]
            Loss function to use for the slice search. If not provided, will use `log_loss` for classification models
            and `mse` for regression models.
        threshold : Optional[float]
            Threshold for the deviation of metrics between slices and the overall dataset. If the deviation is larger
            than the threshold, an issue will be reported.
        alpha : Optional[float]
            Experimental: false discovery rate for issue detection. If a value is provided, false discovery rate will be
            controlled with a Benjamini–Hochberg procedure, and only statistically significant issues will be reported.
            This is disabled by default because only a subset of metrics are currently supported.
        method : Optional[str]
            The slicing method used to find the data slices. Available methods are: `tree`, `bruteforce`, `optimal`,
            `multiscale`. Default is `tree`.
        """
        self.metrics = metrics
        self.threshold = threshold
        self.method = method
        self.alpha = alpha
        self.loss = loss
        super().__init__(**kwargs)

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
    ) -> Sequence[Issue]:
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
            issues = [issue for issue in issues if issue.meta.get("p_value", np.nan) <= p_value_threshold]
            logger.info(f"PerformanceBiasDetector: Kept {len(issues)} significant issues out of {len(p_values)}.")

        # Group issues by slice and keep only the most critical
        issues_by_slice = defaultdict(list)
        for issue in issues:
            issues_by_slice[issue.slicing_fn].append(issue)

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
            slice_dataset, slice_metric, p_value = _calculate_slice_metrics(
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
                level = IssueLevel.MAJOR if abs(relative_delta) > 2 * self.threshold else IssueLevel.MEDIUM
                desc = "For records in the dataset where {slicing_fn}, the {metric} is {abs_deviation_perc}% {comparison_op} than the global {metric}."

                issue = Issue(
                    model=model,
                    dataset=dataset,
                    group=Performance,
                    level=level,
                    description=desc,
                    meta={
                        "metric": slice_metric.name,
                        "metric_value": slice_metric.value,
                        "metric_reference_value": ref_metric.value,
                        "slice_metric": slice_metric,
                        "reference_metric": ref_metric,
                        "deviation": f"{relative_delta*100:+.2f}% than global",
                        "deviation_perc": round(relative_delta * 100, 2),
                        "abs_deviation_perc": round(abs(relative_delta) * 100, 2),
                        "comparison_op": "lower" if metric.greater_is_better else "greater",
                        "slice_size": len(slice_dataset),
                        "threshold": self.threshold,
                        "p_value": p_value,
                    },
                    slicing_fn=slice_fn,
                    importance=-relative_delta if metric.greater_is_better else relative_delta,
                    tests=_generate_performance_tests,
                    taxonomy=["avid-effect:performance:P0204"],
                    detector_name="PerformanceBiasDetector",
                )

                # Add failure examples
                extractor = ExampleExtractor(issue, _filter_examples)
                examples = extractor.get_examples_dataframe(n=20, with_prediction=True)
                issue.add_examples(examples)

                issues.append(issue)

        return issues, p_values


def _filter_examples(issue, dataset):
    pred = issue.model.predict(dataset)
    bad_pred_mask = dataset.df[dataset.target] != pred.prediction

    return dataset.slice(lambda df: df.loc[bad_pred_mask], row_level=False)


_metric_test_mapping = {
    "F1Score": "test_f1",
    "Precision": "test_precision",
    "Accuracy": "test_accuracy",
    "Recall": "test_recall",
    "AUC": "test_auc",
    "MeanSquaredError": "test_mse",
    "MeanAbsoluteError": "test_mae",
}


def _metric_to_test_object(metric: PerformanceMetric):
    from ...testing.tests import performance as performance_tests

    try:
        test_name = _metric_test_mapping[metric.__class__.__name__]
        return getattr(performance_tests, test_name)
    except (KeyError, AttributeError):
        return None


def _generate_performance_tests(issue: Issue):
    metric = issue.meta["slice_metric"].metric
    test_fn = _metric_to_test_object(metric)

    if test_fn is None:
        return dict()

    # Convert the relative threshold to an absolute one.
    delta = (metric.greater_is_better * 2 - 1) * issue.meta["threshold"] * issue.meta["reference_metric"].value
    abs_threshold = issue.meta["reference_metric"].value - delta

    return {
        f"{metric.name} on data slice “{issue.slicing_fn}”": test_fn(
            slicing_function=issue.slicing_fn, threshold=abs_threshold
        )
    }


def _is_unbalanced_target(classes: pd.Series):
    return (classes.value_counts() / classes.count()).std() > 0.2


def _calculate_pvalue_from_contingency_table(slice_metric, comp_metric, max_size_fisher=30):
    ctable = [slice_metric.binary_counts, comp_metric.binary_counts]

    # if the slice size is too small, use Fisher's exact test, otherwise use a G-test
    if min(min(row) for row in ctable) <= max_size_fisher:
        logger.debug("PerformanceBiasDetector: Fisher's exact test")
        return scipy.stats.fisher_exact(ctable, alternative="two-sided")[1]
    logger.debug("PerformanceBiasDetector: G-test")
    return scipy.stats.chi2_contingency(ctable, correction=False, lambda_="log-likelihood")[1]


def _calculate_pvalue_from_permutation_test(
    slice_dataset, comp_dataset, dataset, model, metric, perm_test_resamples=1000
):
    logger.debug("PerformanceBiasDetector: permutation test")

    def statistic(slice_ids, comp_ids):
        perm_slice_dataset = Dataset(
            dataset.df.loc[slice_ids],
            target=dataset.target,
        )
        perm_comp_dataset = Dataset(
            dataset.df.loc[comp_ids],
            target=dataset.target,
        )
        return metric(model, perm_slice_dataset).value - metric(model, perm_comp_dataset).value

    slice_ids = slice_dataset.df.index.values
    comp_ids = comp_dataset.df.index.values
    perm_test_result = scipy.stats.permutation_test(
        (slice_ids, comp_ids),
        statistic=statistic,
        permutation_type="independent",
        n_resamples=perm_test_resamples,
        alternative="two-sided",
    )
    return perm_test_result.pvalue


def _calculate_slice_metrics(
    model, dataset, metric, slice_fn, with_pvalue=False, max_size_fisher=30, perm_test_resamples=1000
):
    slice_dataset = dataset.slice(slice_fn)
    slice_metric = metric(model, slice_dataset)

    if not with_pvalue:
        return slice_dataset, slice_metric, None

    # Perform statistical tests
    comp_dataset = dataset.slice(lambda df: df[~df.index.isin(slice_dataset.df.index)], row_level=False)
    comp_metric = metric(model, comp_dataset)

    try:
        # If we have raw values for the metric, we perform a standard t-test
        logger.debug(f"PerformanceBiasDetector: metric name = {slice_metric.name}")
        if slice_metric.raw_values is not None:
            logger.debug("PerformanceBiasDetector: t-test")
            alternative = "less" if metric.greater_is_better else "greater"
            _, pvalue = scipy.stats.ttest_ind(
                slice_metric.raw_values, comp_metric.raw_values, equal_var=False, alternative=alternative
            )
        elif metric.has_binary_counts:
            # otherwise, this must be classification scores...
            pvalue = _calculate_pvalue_from_contingency_table(slice_metric, comp_metric, max_size_fisher)
        else:
            # if the the contingency table cannot be calculated, do a permutation test
            pvalue = _calculate_pvalue_from_permutation_test(
                slice_dataset, comp_dataset, dataset, model, metric, perm_test_resamples
            )
    except ValueError as err:
        pvalue = np.nan
        logger.debug(f"PerformanceBiasDetector: p-value could not be calculated: {err}")

    logger.debug(f"PerformanceBiasDetector: p-value = {pvalue}")
    return slice_dataset, slice_metric, pvalue
