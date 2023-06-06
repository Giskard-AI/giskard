import logging
from unittest import mock

import pandas as pd
import pytest

from giskard import Dataset
from giskard.scanner.issues import Issue
from giskard.scanner.performance import PerformanceBiasDetector


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
