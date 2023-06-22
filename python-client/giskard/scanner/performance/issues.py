from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from .metrics import PerformanceMetric
from ..common.examples import ExampleExtractor
from ..issues import Issue
from ...datasets.base import Dataset
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...models.base import BaseModel
from ...slicing.slice import QueryBasedSliceFunction
from ...slicing.text_slicer import MetadataSliceFunction


@dataclass
class PerformanceIssueInfo:
    metric: PerformanceMetric
    metric_value_reference: float
    metric_value_slice: float
    slice_fn: SlicingFunction
    slice_size: int
    threshold: float
    p_value: Optional[float] = None

    @property
    def metric_rel_delta(self):
        return (self.metric_value_slice - self.metric_value_reference) / self.metric_value_reference

    @property
    def metric_abs_delta(self):
        return self.metric_value_slice - self.metric_value_reference


class PerformanceIssue(Issue):
    """Performance Issue"""

    group = "Performance"

    info: PerformanceIssueInfo

    def __init__(
        self,
        model: BaseModel,
        dataset: Dataset,
        level: str,
        info: PerformanceIssueInfo,
    ):
        super().__init__(model, dataset, level, info)

    def __repr__(self):
        return f"<PerformanceIssue slice='{self.info.slice_fn}', metric='{self.info.metric.name}', metric_delta={self.info.metric_rel_delta * 100:.2f}%>"

    @property
    def domain(self):
        return str(self.info.slice_fn)

    @property
    def metric(self):
        return f"{self.info.metric.name} = {self.info.metric_value_slice:.2f}"

    @property
    def deviation(self):
        return f"{self.info.metric_rel_delta * 100:+.2f}% than global"

    @property
    def description(self):
        return f"{self.info.slice_size} samples ({self.info.slice_size / len(self.dataset) * 100:.2f}%)"

    @property
    def features(self):
        if isinstance(self.info.slice_fn, QueryBasedSliceFunction):
            return self.info.slice_fn.query.columns()
        if isinstance(self.info.slice_fn, MetadataSliceFunction):
            return [self.info.slice_fn.feature]
        return self.model.meta.feature_names or self.dataset.columns

    @lru_cache
    def examples(self, n=3):
        def filter_examples(issue, dataset):
            pred = issue.model.predict(dataset)
            bad_pred_mask = dataset.df[dataset.target] != pred.prediction

            return dataset.slice(lambda df: df.loc[bad_pred_mask], row_level=False)

        extractor = ExampleExtractor(self, filter_examples)
        return extractor.get_examples_dataframe(n, with_prediction=1)

    @property
    def importance(self):
        if self.info.metric.greater_is_better:
            return -self.info.metric_rel_delta

        return self.info.metric_rel_delta

    @property
    def slicing_fn(self):
        return self.info.slice_fn

    def generate_tests(self, with_names=False) -> list:
        test_fn = _metric_to_test_object(self.info.metric)

        if test_fn is None:
            return []

        # Convert the relative threshold to an absolute one.
        delta = (self.info.metric.greater_is_better * 2 - 1) * self.info.threshold * self.info.metric_value_reference
        abs_threshold = self.info.metric_value_reference - delta

        tests = [
            test_fn(
                model=self.model, dataset=self.dataset, slicing_function=self.info.slice_fn, threshold=abs_threshold
            )
        ]

        if with_names:
            names = [f"{self.info.metric.name} on data slice “{self.info.slice_fn}”"]
            return list(zip(tests, names))

        return tests


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
