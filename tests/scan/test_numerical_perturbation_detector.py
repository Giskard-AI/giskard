import numpy as np
import pandas as pd
import pytest
import giskard
from giskard.scanner.robustness.numerical_perturbation_detector import NumericalPerturbationDetector

class MockClassificationModel:
    def predict(self, dataset):
        # Randomly assign predictions, introducing some variability
        return np.random.choice([0, 1], size=len(dataset))

class MockRegressionModel:
    def predict(self, dataset):
        # For simplicity, use a linear relationship plus some noise
        return (2 * dataset['feature_1'] + 3 * dataset['feature_2'] + np.random.normal(0, 5, len(dataset)))
