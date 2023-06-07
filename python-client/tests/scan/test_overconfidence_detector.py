import numpy as np
import pandas as pd
from unittest import mock
from pytest import approx

from giskard.models.base import ModelPredictionResults
from giskard.scanner.calibration.overconfidence_detector import OverconfidenceDetector


def test_calculation_of_overconfidence_loss():
    detector = OverconfidenceDetector()

    model = mock.MagicMock()
    dataset = mock.MagicMock()

    raw_probs = np.array([[0.2, 0.8, 0.0], [0.1, 0.7, 0.2], [0.3, 0.3, 0.4]])
    model.predict.return_value = ModelPredictionResults(
        raw=raw_probs,
        prediction=["B", "B", "C"],
        raw_prediction=raw_probs,
        probabilities=raw_probs.max(axis=-1),
        all_predictions=None,
    )
    model.meta.classification_labels = ["A", "B", "C"]

    dataset.df = pd.DataFrame(
        {
            "feature": [1, 2, 3],
            "target": ["B", "A", "B"],
        },
        index=["ID1", "ID2", "ID3"],
    )
    dataset.target = "target"

    loss_df = detector._calculate_loss(model, dataset)

    # Only bad predictions should be included
    assert loss_df.index.tolist() == ["ID2", "ID3"]

    # Loss should be the difference between the max probability and the probability of the true label
    assert loss_df.loc["ID2", detector.LOSS_COLUMN_NAME] == approx(0.6)
    assert loss_df.loc["ID3", detector.LOSS_COLUMN_NAME] == approx(0.1)
