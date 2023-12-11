import platform
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from giskard import Dataset, Model
from giskard.ml_worker.exceptions.giskard_exception import GiskardPythonVerException
from giskard.models.function import PredictionFunctionModel


def test_prediction_function_model():
    gsk_model = Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1])
    assert isinstance(gsk_model, PredictionFunctionModel)

    pred = gsk_model.predict(Dataset(df=pd.DataFrame({"x": [1, 2, 3], "y": [1, 1, 0]}), target="y"))

    assert pred.raw.shape == (3, 2)
    assert (pred.raw[:, 1] == 1).all()


def test_prediction_function_upload():
    gsk_model = PredictionFunctionModel(
        lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1]
    )

    import tests.utils

    tests.utils.verify_model_upload(gsk_model, Dataset(df=pd.DataFrame({"x": [1, 2, 3], "y": [1, 0, 1]}), target="y"))


def test_single_feature():
    import datasets
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import Pipeline

    # Load training data
    train_data = datasets.load_dataset("sst2", split="train[:5]").to_pandas()

    preprocessor = TfidfVectorizer(max_features=10, lowercase=False)

    classifier = RandomForestClassifier(n_estimators=10, n_jobs=-1)

    model = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])

    X = train_data.sentence
    y = train_data.label

    model.fit(X, y)

    giskard_dataset = Dataset(
        df=train_data,
        target="label",
        name="review_classification_dataset",
    )

    giskard_model = Model(
        model=model.predict_proba,
        model_type="classification",
        name="review_classifier",
        classification_labels=model.classes_,
        feature_names=["sentence"],
    )

    from giskard.core.model_validation import validate_model

    with pytest.raises(Exception) as e:
        validate_model(giskard_model, giskard_dataset)
    assert e.match(r"Your model returned an error when we passed a 'pandas.Dataframe' as input.*")


COMPAT_TABLE = {
    "3.9": ["3.9", "3.10"],
    "3.10": ["3.9", "3.10"],
    "3.11": ["3.11"],
}
PYTHON_MAJOR_VERSION = ".".join(platform.python_version_tuple()[:2])
BACKWARD_COMPATIBILITY_MODEL_VERSIONS = {"3.9": "3.10", "3.10": "3.10", "3.11": "3.11"}


@pytest.mark.parametrize("py_ver", ["3.9", "3.10", "3.11"])
def test_prediction_function_load(py_ver):
    model_path = Path(__file__).parent / "fixtures" / "func" / py_ver
    if PYTHON_MAJOR_VERSION in COMPAT_TABLE[py_ver]:
        model = Model.load(model_path)
        assert model is not None
    else:
        with pytest.raises(GiskardPythonVerException):
            Model.load(model_path)


@pytest.mark.skipif(
    PYTHON_MAJOR_VERSION not in BACKWARD_COMPATIBILITY_MODEL_VERSIONS,
    reason=f"No model pickled with Python {PYTHON_MAJOR_VERSION} ",
)
def test_ensure_backward_compatibility():
    model_path = (
        Path(__file__).parent / "fixtures" / "ipcc" / BACKWARD_COMPATIBILITY_MODEL_VERSIONS[PYTHON_MAJOR_VERSION]
    )

    import cloudpickle

    with open(model_path / "ModelClass.pkl", "rb") as f:
        ModelCls = cloudpickle.load(f)

    model = ModelCls.load(model_path, ["Added", "arg"], added_kwarg="Should not break")
    assert model is not None

    expected_results = ["foo", "bar", "baz"]

    predictions = model.predict(
        Dataset(pd.DataFrame({"query": expected_results})), ["Added", "arg"], added_kwarg="Should not break"
    ).raw_prediction

    assert list(predictions) == expected_results


if __name__ == "__main__":
    py_ver = PYTHON_MAJOR_VERSION
    model_path = Path(__file__).parent / "fixtures" / "func" / py_ver
    Model(lambda df: np.ones(len(df)), model_type="classification", classification_labels=[0, 1]).save(model_path)
