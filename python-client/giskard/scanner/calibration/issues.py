import pandas as pd
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache

from ...testing.tests.calibration import test_underconfidence_rate

from ...testing.tests.calibration import test_overconfidence_rate

from ..common.examples import ExampleExtractor

from ..issues import Issue
from ...datasets.base import Dataset
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...models.base import BaseModel
from ...slicing.slice import QueryBasedSliceFunction
from ...slicing.text_slicer import MetadataSliceFunction


@dataclass
class CalibrationIssueInfo:
    slice_fn: SlicingFunction
    slice_size: int
    metric_value_slice: float
    metric_value_reference: float
    loss_values: pd.Series
    fail_idx: pd.DataFrame
    threshold: float
    p_threshold: float

    @property
    def metric_rel_delta(self):
        return (self.metric_value_slice - self.metric_value_reference) / self.metric_value_reference

    @property
    def metric_abs_delta(self):
        return self.metric_value_slice - self.metric_value_reference


class CalibrationIssue(Issue):
    group = "Calibration"

    info: CalibrationIssueInfo

    def __init__(
        self,
        model: BaseModel,
        dataset: Dataset,
        level: str,
        info: CalibrationIssueInfo,
    ):
        super().__init__(model, dataset, level, info)

    @property
    def domain(self):
        return str(self.info.slice_fn)

    @property
    @abstractmethod
    def metric(self):
        ...

    @property
    def deviation(self):
        return f"{self.info.metric_rel_delta * 100:.2f}% than global"

    @property
    def description(self):
        return f"{len(self.info.fail_idx)} out of {self.info.slice_size} samples"

    def _features(self):
        if isinstance(self.info.slice_fn, QueryBasedSliceFunction):
            return self.info.slice_fn.query.columns()
        if isinstance(self.info.slice_fn, MetadataSliceFunction):
            return [self.info.slice_fn.feature]
        return self.model.meta.feature_names or self.dataset.columns

    @property
    def importance(self):
        return self.info.metric_rel_delta

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
            bad_pred_mask = dataset.df.index.isin(self.info.fail_idx)

            return dataset.slice(lambda df: df.loc[bad_pred_mask], row_level=False)

        def sort_examples(issue, examples):
            idx = self.info.loss_values.loc[examples.index].sort_values(ascending=False).index
            return examples.loc[idx]

        extractor = ExampleExtractor(self, filter_examples, sort_examples)
        return extractor.get_examples_dataframe(n, with_prediction=2)

    def generate_tests(self, with_names=False) -> list:
        return []


class OverconfidenceIssue(CalibrationIssue):
    group = "Overconfidence"

    @property
    def metric(self) -> str:
        return "Overconfidence rate"

    def generate_tests(self, with_names=False) -> list:
        abs_threshold = self.info.metric_value_reference * (1 + self.info.threshold)

        tests = [
            test_overconfidence_rate(
                model=self.model,
                dataset=self.dataset,
                slicing_function=self.info.slice_fn,
                threshold=abs_threshold,
                p_threshold=self.info.p_threshold,
            )
        ]

        if with_names:
            names = [f"Overconfidence on data slice “{self.info.slice_fn}”"]

            return list(zip(tests, names))

        return tests


class UnderconfidenceIssue(CalibrationIssue):
    group = "Underconfidence"

    _num_labels_display = 2

    @property
    def metric(self) -> str:
        return "Underconfidence rate"

    @property
    def deviation(self):
        return f"{self.info.metric_rel_delta * 100:.2f}% than global"

    def generate_tests(self, with_names=False) -> list:
        abs_threshold = self.info.metric_value_reference * (1 + self.info.threshold)

        tests = [
            test_underconfidence_rate(
                model=self.model,
                dataset=self.dataset,
                slicing_function=self.info.slice_fn,
                threshold=abs_threshold,
                p_threshold=self.info.p_threshold,
            )
        ]

        if with_names:
            names = [f"Underconfidence on data slice “{self.info.slice_fn}”"]

            return list(zip(tests, names))

        return tests
