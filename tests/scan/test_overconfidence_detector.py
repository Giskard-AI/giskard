from unittest import mock

import numpy as np
import pandas as pd
from pytest import approx

import giskard
from giskard.models.base import ModelPredictionResults
from giskard.scanner.calibration.overconfidence_detector import OverconfidenceDetector
from giskard.scanner.issues import IssueLevel, Overconfidence


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


def test_overconfidence_issue_detection():
    dataset = giskard.Dataset(
        pd.DataFrame({"feat": ["a", "b", "c"] * 100, "target": [1, 0, 1] * 100}), target="target", cat_columns=["feat"]
    )

    def prediction_fn(df):
        ps = np.zeros((len(df), 2))
        ps[df.feat == "a"] = [0.1, 0.9]
        ps[df.feat == "b"] = [0.49, 0.51]
        ps[df.feat == "c"] = [0.9, 0.1]
        return ps

    model = giskard.Model(prediction_fn, model_type="classification", classification_labels=[0, 1])

    detector = OverconfidenceDetector()
    issues = detector.run(model, dataset)

    assert len(issues) == 1

    issue = issues[0]
    assert issue.group == Overconfidence
    assert issue.level == IssueLevel.MAJOR

    # Check tests
    tests = issue.generate_tests(with_names=True)
    assert len(tests) == 1

    assert tests[0][1] == 'Overconfidence on data slice “`feat` == "c"”'

    the_test = tests[0][0]
    assert the_test.meta.name == "test_overconfidence_rate"

    # model and dataset are set as default params in `Suite`
    assert "model" not in the_test.params
    the_test.params.update({"model": model})
    assert "dataset" not in the_test.params
    the_test.params.update({"dataset": dataset})

    assert the_test.params["p_threshold"] == approx(0.5)

    # Global rate is 50%, we accept a 10% deviation, thus up to 55%:
    assert the_test.params["threshold"] == approx(1 / 2 * 1.10)

    result = tests[0][0].execute()
    assert result.passed is False
