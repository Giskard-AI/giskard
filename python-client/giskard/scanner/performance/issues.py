from dataclasses import dataclass

from ..issues import Issue
from ...models.base import BaseModel
from ...datasets.base import Dataset
from .metrics import PerformanceMetric
from ...slicing.slice import QueryBasedSliceFunction
from ...slicing.text_slicer import MetadataSliceFunction
from ...ml_worker.testing.registry.slicing_function import SlicingFunction


@dataclass
class PerformanceIssueInfo:
    metric: PerformanceMetric
    metric_value_reference: float
    metric_value_slice: float
    slice_fn: SlicingFunction
    slice_size: int
    threshold: float

    @property
    def metric_rel_delta(self):
        return (self.metric_value_slice - self.metric_value_reference) / self.metric_value_reference

    @property
    def metric_abs_delta(self):
        return self.metric_value_slice - self.metric_value_reference


class PerformanceIssue(Issue):
    """Performance Issue"""

    group = "Performance bias"
    group_message = "We found some data slices in your dataset on which your model performance is lower than average."

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
        return f"{self.info.metric_rel_delta * 100:.2f}% than global"

    @property
    def description(self):
        return f"{self.info.slice_size} samples ({self.info.slice_size / len(self.dataset) * 100:.2f}%)"

    def _features(self):
        if isinstance(self.info.slice_fn, QueryBasedSliceFunction):
            return self.info.slice_fn.query.columns()
        if isinstance(self.info.slice_fn, MetadataSliceFunction):
            return [self.info.slice_fn.feature]
        return self.model.meta.feature_names or self.dataset.columns

    def examples(self, n=3):
        ex_dataset = self.dataset.slice(self.info.slice_fn)
        predictions = self.model.predict(ex_dataset).prediction
        examples = ex_dataset.df.copy()
        bad_pred_mask = examples[self.dataset.target] != predictions
        examples = examples[bad_pred_mask]

        # Keep only interesting columns
        features = self._features()
        cols_to_show = features + [self.dataset.target]
        examples = examples.loc[:, cols_to_show]

        # If metadata slice, add the metadata column
        if isinstance(self.info.slice_fn, MetadataSliceFunction):
            for col in features:
                meta_cols = self.info.slice_fn.query.columns()
                provider = self.info.slice_fn.provider
                for meta_col in meta_cols:
                    meta_vals = self.dataset.column_meta[col, provider].loc[examples.index, meta_col]
                    examples.insert(
                        loc=examples.columns.get_loc(col) + 1,
                        column=f"{meta_col}({col})",
                        value=meta_vals,
                        allow_duplicates=True,
                    )

        # Add the model prediction
        examples[f"Predicted `{self.dataset.target}`"] = predictions[bad_pred_mask]

        n = min(len(examples), n)
        if n > 0:
            return examples.sample(n, random_state=142)

        return examples

    @property
    def importance(self):
        if self.info.metric.greater_is_better:
            return -self.info.metric_rel_delta

        return self.info.metric_rel_delta

    def generate_tests(self) -> list:
        test_fn = _metric_to_test_object(self.info.metric)

        if test_fn is None:
            return []

        # Convert the relative threshold to an absolute one.
        delta = (self.info.metric.greater_is_better * 2 - 1) * self.info.threshold * self.info.metric_value_reference
        abs_threshold = self.info.metric_value_reference - delta

        return [test_fn(self.model, self.dataset, self.info.slice_fn, abs_threshold)]


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
    from ...ml_worker.testing.tests import performance as performance_tests

    try:
        test_name = _metric_test_mapping[metric.__class__.__name__]
        return getattr(performance_tests, test_name)
    except (KeyError, AttributeError):
        return None
