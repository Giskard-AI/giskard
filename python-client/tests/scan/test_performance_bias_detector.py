import pytest
import logging
import pandas as pd
from unittest import mock

from giskard import Dataset
from giskard.scanner.issues import Issue
from giskard.scanner.performance import PerformanceBiasDetector
from giskard.scanner.performance.performance_bias_detector import _calculate_slice_metrics


def test_performance_bias_detector_skips_small_datasets(german_credit_model, german_credit_data, caplog):
    small_dataset = german_credit_data.slice(lambda df: df.sample(50), row_level=False)
    detector = PerformanceBiasDetector()
    with caplog.at_level(logging.WARNING):
        issues = detector.run(german_credit_model, small_dataset)
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
        detector.run(german_credit_model, large_dataset)
    except ValueError:
        pass

    assert large_dataset.slice.called
    assert large_dataset.df.sample.assert_called_once

    normal_dataset = mock.MagicMock(german_credit_data)
    normal_dataset.__len__.return_value = 10_000

    detector = PerformanceBiasDetector()
    try:
        detector.run(german_credit_model, normal_dataset)
    except ValueError:
        pass

    assert normal_dataset.slice.not_called


def test_performance_bias_detector_with_tabular(german_credit_model, german_credit_data):
    detector = PerformanceBiasDetector()

    issues = detector.run(german_credit_model, german_credit_data)
    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])


@pytest.mark.slow
def test_performance_bias_detector_with_text_features(enron_model, enron_data):
    # Augment the dataset with random data
    df = pd.DataFrame({col: enron_data.df[col].sample(500, replace=True).values for col in enron_data.columns})
    dataset = Dataset(df, target=enron_data.target, column_types=enron_data.column_types)
    detector = PerformanceBiasDetector()

    issues = detector.run(enron_model, dataset)
    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])


def test_calculate_slice_metrics():
    # Create a mock model and dataset
    model = mock.MagicMock()
    dataset = Dataset(pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}), target="y")

    def metric(model, dataset):
        if len(dataset) == 2:  # slice
            return mock.MagicMock(value=0.4, affected_samples=11, raw_values=None)

        return mock.MagicMock(value=0.46, affected_samples=32, raw_values=None)

    metric.greater_is_better = True

    # Without p-value
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(model, dataset, metric, lambda df: df["x"] > 1)

    assert sliced_dataset.df.y.tolist() == [5, 6]
    assert slice_metric.value == 0.4
    assert slice_metric.affected_samples == 11
    assert pvalue is None

    # With p-value
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(
        model, dataset, metric, lambda df: df["x"] > 1, with_pvalue=True
    )

    assert sliced_dataset.df.y.tolist() == [5, 6]
    assert slice_metric.value == 0.4
    assert slice_metric.affected_samples == 11
    assert pvalue == pytest.approx(0.80, abs=0.01)

    # For regression
    def metric(model, dataset):
        if len(dataset) == 2:  # slice
            return mock.MagicMock(value=0.4, affected_samples=5, raw_values=[1, 2, 3, 1, 2])

        return mock.MagicMock(value=0.46, affected_samples=7, raw_values=[2, 2, 2, 1, 2, 2, 2])

    metric.greater_is_better = True
    sliced_dataset, slice_metric, pvalue = _calculate_slice_metrics(
        model, dataset, metric, lambda df: df["x"] > 1, with_pvalue=True
    )

    assert sliced_dataset.df.y.tolist() == [5, 6]
    assert slice_metric.value == 0.4
    assert pvalue == pytest.approx(0.44, abs=0.01)
