import numpy as np
import pandas as pd
import pytest

import giskard
from giskard.scanner.robustness.numerical_perturbation_detector import NumericalPerturbationDetector


class MockClassificationModel:
    def predict(self, df):
        # Randomly assign predictions, introducing some variability
        return np.random.choice([0, 1], size=len(df))


class MockRegressionModel:
    def predict(self, df):
        # For simplicity, use a linear relationship plus some noise
        return 2 * df["feature_1"] + 3 * df["feature_2"] + np.random.normal(0, 5, len(df))


def test_numerical_perturbation_classification():
    # Creating a simple mock classification dataset
    df = pd.DataFrame(
        {"feature_1": [1.0, 2.0, 3.0, 4.0, 5.0], "feature_2": [10.0, 20.0, 30.0, 40.0, 50.0], "target": [0, 1, 1, 0, 0]}
    )
    dataset = giskard.Dataset(df=df, target="target", column_types={"feature_1": "numeric", "feature_2": "numeric"})

    # Creating a mock model with some variability in predictions
    model = giskard.Model(MockClassificationModel().predict, model_type="classification", classification_labels=[0, 1])

    # Running the Numerical Perturbation Detector
    analyzer = NumericalPerturbationDetector(threshold=0.01)
    issues = analyzer.run(model, dataset, features=["feature_1", "feature_2"])

    assert issues  # Ensure that the detector identifies some issues


def test_numerical_perturbation_skips_non_numerical_dtypes():
    # Mock dataset with a text feature, but declared as numeric
    df = pd.DataFrame({"feature": ["a", "b", "c", "d", "e"], "target": [0, 1, 0, 1, 0]})
    dataset = giskard.Dataset(df, target="target", column_types={"feature": "text"})

    # Creating a mock model that always predicts 1
    model = giskard.Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1])

    # Running the Numerical Perturbation Detector
    analyzer = NumericalPerturbationDetector(threshold=0.001, output_sensitivity=1.0, num_samples=100)
    issues = analyzer.run(model, dataset, features=["feature"])

    assert not issues  # Since the feature is non-numeric, no issues should be detected


def test_numerical_perturbation_works_with_nan_values():
    # Mock dataset with NaN values in numeric feature
    df = pd.DataFrame({"feature": [1.0, 2.0, np.nan, 4.0, 5.0], "target": [0, 1, 0, 1, 0]})
    dataset = giskard.Dataset(df, target="target", column_types={"feature": "numeric"})

    # Creating a mock model with some variability in predictions
    model = giskard.Model(
        lambda df: np.random.choice([0, 1], size=len(df)), model_type="classification", classification_labels=[0, 1]
    )

    # Running the Numerical Perturbation Detector
    analyzer = NumericalPerturbationDetector(threshold=0.01)
    issues = analyzer.run(model, dataset, features=["feature"])

    assert issues  # Ensure that the detector identifies some issues


@pytest.mark.memory_expensive
def test_numerical_perturbation_on_regression():
    # Mock regression dataset
    df = pd.DataFrame(
        {
            "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature_2": [10.0, 20.0, 30.0, 40.0, 50.0],
            "target": [15.0, 25.0, 35.0, 45.0, 55.0],
        }
    )
    dataset = giskard.Dataset(df, target="target", column_types={"feature_1": "numeric", "feature_2": "numeric"})

    # Creating a mock model with a linear relationship
    model = giskard.Model(MockRegressionModel().predict, model_type="regression")

    # Running the Numerical Perturbation Detector
    analyzer = NumericalPerturbationDetector(threshold=0.01, output_sensitivity=0.1)
    issues = analyzer.run(model, dataset, features=["feature_1", "feature_2"])

    assert issues  # Ensure that the detector identifies some issues
