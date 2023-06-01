import pytest
import pandas as pd
from giskard import wrap_dataset
from giskard.scanner.issues import Issue
from giskard.scanner.performance import ModelBiasDetector


def test_model_bias_detector_skips_small_datasets(german_credit_model, german_credit_data):
    small_dataset = german_credit_data.slice(lambda df: df.sample(50), row_level=False)
    detector = ModelBiasDetector()
    with pytest.warns(match="Skipping model bias scan"):
        issues = detector.run(german_credit_model, small_dataset)
    assert len(issues) == 0


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
