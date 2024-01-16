from typing import Optional

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass

import numpy as np
import sklearn.metrics

from ...datasets.base import Dataset
from ...models.base import BaseModel


@dataclass
class MetricResult:
    metric: "PerformanceMetric"
    value: float
    affected_samples: int
    raw_values: Optional[np.ndarray] = None
    binary_counts: Optional[list[int]] = None

    @property
    def name(self):
        return self.metric.name

    def __str__(self):
        return f"{self.name} = {self.value:.3f}"


class PerformanceMetric(ABC):
    name: str
    greater_is_better = True
    has_binary_counts = False

    @abstractmethod
    def __call__(self, model: BaseModel, dataset: Dataset) -> MetricResult:
        ...


class ClassificationPerformanceMetric(PerformanceMetric, metaclass=ABCMeta):
    def __call__(self, model: BaseModel, dataset: Dataset) -> MetricResult:
        if not model.is_classification:
            raise ValueError(f"Metric '{self.name}' is only defined for classification models.")

        y_true = np.asarray(dataset.df[dataset.target])
        y_pred = np.asarray(model.predict(dataset).prediction)

        value = self._calculate_metric(y_true, y_pred, model)
        num_affected = self._calculate_affected_samples(y_true, y_pred, model)
        binary_counts = self._calculate_binary_counts(value, num_affected) if self.has_binary_counts else None

        return MetricResult(self, value, num_affected, binary_counts=binary_counts)

    @abstractmethod
    def _calculate_metric(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel) -> MetricResult:
        ...

    def _calculate_affected_samples(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel) -> int:
        return len(y_true)

    def _calculate_binary_counts(self, value, num_affected) -> list[int]:
        x = round(value * num_affected)
        y = num_affected - x
        return [x, y]


class Accuracy(ClassificationPerformanceMetric):
    name = "Accuracy"
    greater_is_better = True
    has_binary_counts = True

    def _calculate_metric(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel):
        return sklearn.metrics.accuracy_score(y_true, y_pred)


class BalancedAccuracy(ClassificationPerformanceMetric):
    name = "Balanced Accuracy"
    greater_is_better = True
    has_binary_counts = False

    def _calculate_metric(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel):
        return sklearn.metrics.balanced_accuracy_score(y_true, y_pred)


class SklearnClassificationScoreMixin:
    _sklearn_metric: str

    def _calculate_metric(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel):
        metric_fn = getattr(sklearn.metrics, self._sklearn_metric)
        if model.is_binary_classification:
            return metric_fn(
                y_true,
                y_pred,
                labels=model.meta.classification_labels,
                pos_label=model.meta.classification_labels[1],
                average="binary",
            )

        return metric_fn(y_true, y_pred, labels=model.meta.classification_labels, average="micro")


class F1Score(SklearnClassificationScoreMixin, ClassificationPerformanceMetric):
    name = "F1 Score"
    greater_is_better = True
    has_binary_counts = False
    _sklearn_metric = "f1_score"

    def _calculate_affected_samples(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel) -> int:
        if model.is_binary_classification:
            # F1 score will not be affected by true negatives
            neg = model.meta.classification_labels[0]
            tn = ((y_true == neg) & (y_pred == neg)).sum()
            return len(y_true) - tn

        return len(y_true)


class Precision(SklearnClassificationScoreMixin, ClassificationPerformanceMetric):
    name = "Precision"
    greater_is_better = True
    has_binary_counts = True
    _sklearn_metric = "precision_score"

    def _calculate_affected_samples(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel) -> int:
        if model.is_binary_classification:
            return (y_pred == model.meta.classification_labels[1]).sum()

        return len(y_true)


class Recall(SklearnClassificationScoreMixin, ClassificationPerformanceMetric):
    name = "Recall"
    greater_is_better = True
    has_binary_counts = True
    _sklearn_metric = "recall_score"

    def _calculate_affected_samples(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel) -> int:
        if model.is_binary_classification:
            return (y_true == model.meta.classification_labels[1]).sum()

        return len(y_true)


class AUC(PerformanceMetric):
    name = "ROC AUC"
    greater_is_better = True
    has_binary_counts = False

    def __call__(self, model: BaseModel, dataset: Dataset) -> MetricResult:
        y_true = dataset.df[dataset.target]
        if model.is_binary_classification:
            y_score = model.predict(dataset).raw[:, 1]
        else:
            y_score = model.predict(dataset).all_predictions

        value = sklearn.metrics.roc_auc_score(
            y_true, y_score, multi_class="ovo", labels=model.meta.classification_labels
        )

        return MetricResult(self, value, len(y_true))


class RegressionPerformanceMetric(PerformanceMetric):
    def __call__(self, model: BaseModel, dataset: Dataset) -> MetricResult:
        if not model.is_regression:
            raise ValueError(f"Metric '{self.name}' is only defined for regression models.")

        y_true = dataset.df[dataset.target]
        y_pred = model.predict(dataset).prediction

        value = self._calculate_metric(y_true, y_pred, model)
        return MetricResult(self, value, len(y_true))

    @abstractmethod
    def _calculate_metric(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel) -> float:
        ...


class SklearnRegressionScoreMixin:
    _sklearn_metric: str

    def _calculate_metric(self, y_true: np.ndarray, y_pred: np.ndarray, model: BaseModel):
        metric_fn = getattr(sklearn.metrics, self._sklearn_metric)
        return metric_fn(y_true, y_pred)


class MeanSquaredError(SklearnRegressionScoreMixin, RegressionPerformanceMetric):
    name = "MSE"
    greater_is_better = False
    _sklearn_metric = "mean_squared_error"


class MeanAbsoluteError(SklearnRegressionScoreMixin, RegressionPerformanceMetric):
    name = "MAE"
    greater_is_better = False
    _sklearn_metric = "mean_absolute_error"


_metrics_register = {
    "f1": F1Score,
    "accuracy": Accuracy,
    "precision": Precision,
    "recall": Recall,
    "auc": AUC,
    "balanced_accuracy": BalancedAccuracy,
    "mse": MeanSquaredError,
    "mae": MeanAbsoluteError,
}


def get_metric(metric_name: str):
    if isinstance(metric_name, PerformanceMetric):
        return metric_name

    metric_cls = _metrics_register.get(metric_name)
    if not metric_cls:
        raise ValueError(f"Unknown metric '{metric_name}'")

    return metric_cls()
