import numpy as np
import pandas as pd

from giskard import Dataset, Model
from giskard.scanner.issues import Stochasticity
from giskard.scanner.stochasticity.stochasticity_detector import StochasticityDetector


def _make_random_classification_model(n_labels=3):
    def random_predictor(df):
        return np.random.normal(size=(len(df), n_labels))

    return Model(
        random_predictor,
        model_type="classification",
        classification_labels=np.arange(n_labels),
    )


def test_stochasticity_detector_works_on_small_dataset(enron_data, enron_model):
    small_dataset = enron_data.slice(lambda df: df.sample(10), row_level=False)
    detector = StochasticityDetector()
    issues = detector.run(enron_model, small_dataset)

    # should detect no issues
    assert not issues

    random_model = _make_random_classification_model()
    issues = detector.run(random_model, small_dataset)

    # should detect stochasticity
    assert len(issues) == 1


def test_stochasticity_is_detected():
    def random_predictor(df):
        return np.random.normal(size=(len(df), 3))

    model = Model(
        random_predictor,
        model_type="classification",
        classification_labels=["A", "B", "C"],
    )

    dataset = Dataset(pd.DataFrame({"feature": [1, 2, 3]}), target=None)

    detector = StochasticityDetector()
    issues = detector.run(model, dataset)

    assert len(issues) == 1
    assert issues[0].group == Stochasticity
