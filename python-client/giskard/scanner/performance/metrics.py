import sklearn.metrics
from abc import ABC, ABCMeta, abstractmethod

from ...models.base import BaseModel
from ...datasets.base import Dataset


class PerformanceMetric(ABC):
    name: str
    greater_is_better = True

    @abstractmethod
    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        ...


class ClassificationPerformanceMetric(PerformanceMetric, metaclass=ABCMeta):
    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        if not model.is_classification:
            raise ValueError(f"Metric '{self.name}' is only defined for classification models.")

        y_true = dataset.df[dataset.target]
        y_pred = model.predict(dataset).prediction

        return self._calculate_metric(y_true, y_pred, model)

    @abstractmethod
    def _calculate_metric(self, y_true, y_pred, model: BaseModel) -> float:
        ...


class Accuracy(ClassificationPerformanceMetric):
    name = "Accuracy"
    greater_is_better = True

    def _calculate_metric(self, y_true, y_pred, model: BaseModel):
        return sklearn.metrics.accuracy_score(y_true, y_pred)


class BalancedAccuracy(ClassificationPerformanceMetric):
    name = "Balanced Accuracy"
    greater_is_better = True

    def _calculate_metric(self, y_true, y_pred, model: BaseModel):
        return sklearn.metrics.balanced_accuracy_score(y_true, y_pred)


class SklearnClassificationScoreMixin:
    _sklearn_metric: str

    def _calculate_metric(self, y_true, y_pred, model: BaseModel):
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
    _sklearn_metric = "f1_score"


class Precision(SklearnClassificationScoreMixin, ClassificationPerformanceMetric):
    name = "Precision"
    greater_is_better = True
    _sklearn_metric = "precision_score"


class Recall(SklearnClassificationScoreMixin, ClassificationPerformanceMetric):
    name = "Recall"
    greater_is_better = True
    _sklearn_metric = "recall_score"


class AUC(PerformanceMetric):
    name = "ROC AUC"
    greater_is_better = True

    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        y_true = dataset.df[dataset.target]
        if model.is_binary_classification:
            y_score = model.predict(dataset).raw[:, 1]
        else:
            y_score = model.predict(dataset).all_predictions

        return sklearn.metrics.roc_auc_score(
            y_true,
            y_score,
            multi_class="ovo",
            labels=model.meta.classification_labels,
        )


class RegressionPerformanceMetric(PerformanceMetric):
    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        if not model.is_regression:
            raise ValueError(f"Metric '{self.name}' is only defined for regression models.")

        y_true = dataset.df[dataset.target]
        y_pred = model.predict(dataset).prediction

        return self._calculate_metric(y_true, y_pred, model)

    @abstractmethod
    def _calculate_metric(self, y_true, y_pred, model: BaseModel) -> float:
        ...


class SklearnRegressionScoreMixin:
    _sklearn_metric: str

    def _calculate_metric(self, y_true, y_pred, model: BaseModel):
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
