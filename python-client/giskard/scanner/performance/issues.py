from dataclasses import dataclass

from ..issues import Issue, IssueInfo
from ...models.base import _BaseModel
from ... import Dataset
from .metrics import PerformanceMetric
from ...ml_worker.testing.registry.slicing_function import SlicingFunction


@dataclass
class PerformanceIssueInfo(IssueInfo):
    metric: PerformanceMetric
    metric_value_reference: float
    metric_value_slice: float
    slice_fn: SlicingFunction
    slice_size: int

    @property
    def metric_rel_delta(self):
        return (self.metric_value_slice - self.metric_value_reference) / self.metric_value_reference

    @property
    def metric_abs_delta(self):
        return self.metric_value_slice - self.metric_value_reference


class PerformanceIssue(Issue):
    """Performance Issue"""

    group = "_Model bias"
    info: PerformanceIssueInfo

    def __init__(
        self,
        model: _BaseModel,
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
        return self.info.metric.name

    @property
    def deviation(self):
        return f"{self.info.metric_rel_delta * 100:.2f}% than global"

    @property
    def description(self):
        return f"{self.info.slice_size} samples ({self.info.slice_size / len(self.dataset) * 100:.2f}%)"

    def examples(self, n=3):
        # @TODO: improve this once we support metadata
        ex_dataset = self.dataset.slice(self.info.slice_fn)
        predictions = self.model.predict(ex_dataset).prediction
        examples = ex_dataset.df.copy()
        examples["predicted_label"] = predictions
        examples = examples[examples[self.dataset.target] != examples["predicted_label"]]

        n = min(len(examples), n)
        if n > 0:
            return examples.sample(n, random_state=142)

        return examples

    @property
    def importance(self):
        if self.info.metric.greater_is_better:
            return -self.info.metric_rel_delta

        return self.info.metric_rel_delta
