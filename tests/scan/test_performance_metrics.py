import pytest
import numpy as np
import pandas as pd
import sklearn.metrics
from pytest import approx
from giskard.scanner.performance import metrics
from giskard import Model, Dataset


def test_classification_metrics_fail_on_regression_model(linear_regression_diabetes, diabetes_dataset_with_target):
    for metric in [
        metrics.F1Score,
        metrics.Precision,
        metrics.Recall,
        metrics.AUC,
        metrics.Accuracy,
        metrics.BalancedAccuracy,
    ]:
        with pytest.raises(ValueError):
            m = metric()
            m(linear_regression_diabetes, diabetes_dataset_with_target)


@pytest.mark.parametrize(
    "num_classes,metric,reference_metric,reference_kwargs",
    [
        # Binary classification
        (2, metrics.F1Score(), sklearn.metrics.f1_score, dict(average="binary")),
        (2, metrics.Precision(), sklearn.metrics.precision_score, dict(average="binary")),
        (2, metrics.Recall(), sklearn.metrics.recall_score, dict(average="binary")),
        (2, metrics.Accuracy(), sklearn.metrics.accuracy_score, dict()),
        (2, metrics.BalancedAccuracy(), sklearn.metrics.balanced_accuracy_score, dict()),
        # Multiclass classification
        (5, metrics.F1Score(), sklearn.metrics.f1_score, dict(average="micro")),
        (3, metrics.Precision(), sklearn.metrics.precision_score, dict(average="micro")),
        (4, metrics.Recall(), sklearn.metrics.recall_score, dict(average="micro")),
        (4, metrics.Accuracy(), sklearn.metrics.accuracy_score, dict()),
        (5, metrics.BalancedAccuracy(), sklearn.metrics.balanced_accuracy_score, dict()),
    ],
)
def test_multiclass_classification_metrics(num_classes, metric, reference_metric, reference_kwargs):
    classes = np.arange(num_classes)
    rng = np.random.default_rng(111)

    correct_prob = rng.random(size=(100, num_classes))
    correct_prob /= correct_prob.sum(axis=-1, keepdims=True)
    model_prob = rng.random(size=(100, num_classes))
    model_prob /= model_prob.sum(axis=-1, keepdims=True)

    correct_model = Model(lambda _: correct_prob, model_type="classification", classification_labels=classes)
    wrong_model = Model(lambda _: 1 - correct_prob, model_type="classification", classification_labels=classes)
    random_model = Model(lambda _: model_prob, model_type="classification", classification_labels=classes)
    dataset = Dataset(
        df=pd.DataFrame({"demo": np.ones(correct_prob.shape[0]), "label": correct_prob.argmax(axis=-1)}), target="label"
    )

    assert metric(correct_model, dataset).value == approx(1.0)
    assert metric(wrong_model, dataset).value == approx(0.0)
    assert metric(random_model, dataset).value == approx(
        reference_metric(correct_prob.argmax(axis=-1), model_prob.argmax(axis=-1), **reference_kwargs)
    )


def test_auc_metric():
    rng = np.random.default_rng(111)
    y_true = rng.integers(0, 3, size=(100,))

    model_prob = rng.random(size=(100, 3))
    model_prob /= model_prob.sum(axis=-1, keepdims=True)

    model = Model(lambda _: model_prob, model_type="classification", classification_labels=[0, 1, 2])
    dataset = Dataset(df=pd.DataFrame({"demo": np.ones(y_true.shape[0]), "label": y_true}), target="label")
    expected = approx(sklearn.metrics.roc_auc_score(y_true, model_prob, multi_class="ovo"))

    assert metrics.AUC()(model, dataset).value == expected
