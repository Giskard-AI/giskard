import pandas as pd
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import numpy as np

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
    threshold: float

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
        return f"{self.info.slice_size} samples ({self.info.slice_size / len(self.dataset) * 100:.2f}%)"

    def _features(self):
        if isinstance(self.info.slice_fn, QueryBasedSliceFunction):
            return self.info.slice_fn.query.columns()
        if isinstance(self.info.slice_fn, MetadataSliceFunction):
            return [self.info.slice_fn.feature]
        return self.model.meta.feature_names or self.dataset.columns

    @property
    def importance(self):
        return self.info.metric_rel_delta

    @lru_cache
    def examples(self, n=3):
        ex_dataset = self.dataset.slice(self.info.slice_fn)
        model_pred = self.model.predict(ex_dataset)
        predictions = model_pred.prediction
        bad_pred_mask = ex_dataset.df[self.dataset.target] != predictions
        examples = ex_dataset.df[bad_pred_mask].copy()

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
        if model_pred.probabilities is not None:
            num_labels_to_print = min(
                len(self.model.meta.classification_labels), getattr(self, "_num_labels_display", 1)
            )

            pred_examples = []
            for n, ps in enumerate(model_pred.raw[bad_pred_mask]):
                label_idx = np.argsort(-ps)[:num_labels_to_print]
                pred_examples.append(
                    "\n".join([f"{self.model.meta.classification_labels[i]} (p = {ps[i]:.2f})" for i in label_idx])
                )
        else:
            pred_examples = predictions[bad_pred_mask]

        examples[f"Predicted `{self.dataset.target}`"] = pred_examples

        n = min(len(examples), n)
        if n > 0:
            idx = self.info.loss_values.loc[examples.index].nlargest(n).index
            return examples.loc[idx]

        return examples

    def generate_tests(self) -> list:
        return []


class OverconfidenceIssue(CalibrationIssue):
    group = "Overconfidence"

    @property
    def metric(self) -> str:
        return "Overconfidence"


class UnderconfidenceIssue(CalibrationIssue):
    group = "Underconfidence"

    _num_labels_display = 2

    @property
    def metric(self) -> str:
        return "Underconfidence"
