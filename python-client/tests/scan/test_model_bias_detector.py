import logging
import pandas as pd
from unittest import mock
from giskard import wrap_dataset
from giskard.scanner.issues import Issue
from giskard.scanner.performance import ModelBiasDetector


def test_model_bias_detector_skips_small_datasets(german_credit_model, german_credit_data, caplog):
    small_dataset = german_credit_data.slice(lambda df: df.sample(50), row_level=False)
    detector = ModelBiasDetector()
    with caplog.at_level(logging.WARNING):
        issues = detector.run(german_credit_model, small_dataset)
    record = caplog.records[-1]

    assert len(issues) == 0
    assert record.levelname == "WARNING"
    assert "Skipping scan because the dataset is too small" in record.message


def test_model_bias_detector_trims_large_dataset(german_credit_model, german_credit_data):
    # This test could be improved, needs more decoupling in the model bias detector
    large_dataset = mock.MagicMock(german_credit_data)
    large_dataset.__len__.return_value = 10_000_000

    detector = ModelBiasDetector()
    try:
        detector.run(german_credit_model, large_dataset)
    except ValueError:
        pass

    assert large_dataset.slice.called
    assert large_dataset.df.sample.assert_called_once

    normal_dataset = mock.MagicMock(german_credit_data)
    normal_dataset.__len__.return_value = 10_000

    detector = ModelBiasDetector()
    try:
        detector.run(german_credit_model, normal_dataset)
    except ValueError:
        pass

    assert normal_dataset.slice.not_called


def test_model_bias_detector_with_tabular(german_credit_model, german_credit_data):
    detector = ModelBiasDetector()

    issues = detector.run(german_credit_model, german_credit_data)
    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])


def test_model_bias_detector_with_text_features(enron_model, enron_data):
    # Augment the dataset with random data
    df = pd.DataFrame({col: enron_data.df[col].sample(500, replace=True).values for col in enron_data.columns})
    dataset = wrap_dataset(df, target=enron_data.target, column_types=enron_data.column_types)
    detector = ModelBiasDetector()

    issues = detector.run(enron_model, dataset)
    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])
