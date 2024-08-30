import logging
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from giskard import Dataset
from giskard.scanner.issues import Issue
from giskard.scanner.performance import PerformanceBiasDetector
from giskard.scanner.performance.performance_bias_detector import _calculate_slice_metrics


def test_performance_bias_detector_skips_small_datasets(german_credit_model, german_credit_data, caplog):
    small_dataset = german_credit_data.slice(lambda df: df.sample(50), row_level=False)
    detector = PerformanceBiasDetector()
    with caplog.at_level(logging.WARNING):
        issues = detector.run(german_credit_model, small_dataset, features=german_credit_model.feature_names)
    record = caplog.records[-1]

    assert len(issues) == 0
    assert record.levelname == "WARNING"
    assert "Skipping scan because the dataset is too small" in record.message


def test_performance_bias_detector_trims_large_dataset(german_credit_model, german_credit_data):
    # This test could be improved, needs more decoupling in the model bias detector
    large_dataset = mock.MagicMock(german_credit_data)
    large_dataset.__len__.return_value = 10_000_000

    detector = PerformanceBiasDetector()
    try:
        detector.run(german_credit_model, large_dataset, features=german_credit_model.feature_names)
    except (ValueError, TypeError):
        pass
    assert large_dataset.slice.called
    assert large_dataset.df.sample.assert_called_once

    normal_dataset = mock.MagicMock(german_credit_data)
    normal_dataset.__len__.return_value = 10_000

    detector = PerformanceBiasDetector()
    try:
        detector.run(german_credit_model, normal_dataset, features=german_credit_model.feature_names)
    except (ValueError, TypeError):
        pass

    normal_dataset.slice.assert_not_called()


def test_performance_bias_detector_with_tabular(german_credit_model, german_credit_data):
    detector = PerformanceBiasDetector()

    issues = detector.run(german_credit_model, german_credit_data, features=german_credit_model.feature_names)
    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])

    # Check that descriptions are coherent
    assert (
        issues[0].description
        == 'For records in the dataset where `purpose` == "business", the Precision is 5.33% lower than the global Precision.'
    )
    for issue in issues:
        assert issue.meta["metric"] in issue.description
        assert f'{issue.meta["abs_deviation_perc"]}%' in issue.description
        assert str(issue.slicing_fn) in issue.description


@pytest.mark.memory_expensive
def test_performance_bias_detector_with_text_features(enron_model, enron_data):
    # Augment the dataset with random data
    df = pd.DataFrame({col: enron_data.df[col].sample(100, replace=True).values for col in enron_data.columns})
    dataset = Dataset(df, target=enron_data.target, column_types=enron_data.column_types)
    detector = PerformanceBiasDetector()

    issues = detector.run(enron_model, dataset, enron_model.feature_names)
    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])


@pytest.mark.memory_expensive
def test_selects_issues_with_benjamini_hochberg(titanic_model, titanic_dataset):
    # By default, it does not use the statistical significance
    detector = PerformanceBiasDetector()

    issues = detector.run(titanic_model, titanic_dataset, features=["Name", "Sex", "Pclass"])
    assert len(issues) == 6

    # Setting alpha enables the Benjamini–Hochberg procedure
    detector = PerformanceBiasDetector(alpha=0.10)

    issues = detector.run(titanic_model, titanic_dataset, features=["Name", "Sex", "Pclass"])
    assert len(issues) == 3

    detector = PerformanceBiasDetector(alpha=1e-15)

    issues = detector.run(titanic_model, titanic_dataset, features=["Name", "Sex", "Pclass"])
    assert len(issues) == 2


def test_calculate_slice_metrics():
    SLICE_SIZE = 500
    rng = np.random.RandomState(42)

    # Create a mock model and dataset
    model = mock.MagicMock()
    dataset = Dataset(pd.DataFrame({"x": np.arange(5001), "y": rng.randint(1, 6, 5001)}), target="y")

    def metric(model, dataset):
        # About 20% on large datasets
        value = (dataset.df.y % 5 == 0).sum() / len(dataset)
        affected_samples = len(dataset)
        raw_values = None
        x = round(value * affected_samples)
        y = affected_samples - x
        binary_counts = [x, y]
        return mock.MagicMock(
            value=value, affected_samples=affected_samples, raw_values=raw_values, binary_counts=binary_counts
        )

    # Without p-value
    metric.greater_is_better = True
    metric.has_binary_counts = True
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(model, dataset, metric, lambda df: df["x"] <= 9)

    assert sliced_dataset.df.y.count() == 10
    assert slice_metric.value == pytest.approx(0.40, abs=0.02)
    assert slice_metric.affected_samples == 10
    assert pvalue is None

    # With p-value - G-test
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(
        model,
        dataset,
        metric,
        lambda df: df["x"] <= SLICE_SIZE,
        with_pvalue=True,
        max_size_fisher=1,
        perm_test_resamples=1000,
    )

    assert sliced_dataset.df.y.count() == SLICE_SIZE + 1
    assert slice_metric.value == pytest.approx(0.20, abs=0.02)
    assert slice_metric.affected_samples == SLICE_SIZE + 1
    assert pvalue == pytest.approx(0.28, abs=0.05)

    # With p-value - Fisher's exact test
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(
        model,
        dataset,
        metric,
        lambda df: df["x"] <= SLICE_SIZE,
        with_pvalue=True,
        max_size_fisher=1000,
        perm_test_resamples=1000,
    )

    assert sliced_dataset.df.y.count() == SLICE_SIZE + 1
    assert slice_metric.value == pytest.approx(0.20, abs=0.02)
    assert slice_metric.affected_samples == SLICE_SIZE + 1
    assert pvalue == pytest.approx(0.28, abs=0.05)  # should be about the same as G-test

    # With p-value - Permutation test
    metric.has_binary_counts = False
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(
        model,
        dataset,
        metric,
        lambda df: df["x"] <= SLICE_SIZE,
        with_pvalue=True,
        max_size_fisher=1,
        perm_test_resamples=1000,
    )

    assert slice_metric.value == pytest.approx(0.20, abs=0.02)
    assert slice_metric.affected_samples == SLICE_SIZE + 1
    assert pvalue == pytest.approx(0.28, abs=0.05)  # should be about the same as G-test and Fisher test

    # For regression
    def metric(model, dataset):
        if len(dataset) == 10:  # slice
            return mock.MagicMock(value=0.4, affected_samples=5, raw_values=[1, 2, 3, 1, 2])

        return mock.MagicMock(value=0.46, affected_samples=7, raw_values=[2, 2, 2, 1, 2, 2, 2])

    metric.greater_is_better = True
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(
        model, dataset, metric, lambda df: df["x"] <= 9, with_pvalue=True
    )

    assert sliced_dataset.df.y.count() == 10
    assert slice_metric.value == 0.4
    assert pvalue == pytest.approx(0.44, abs=0.01)
