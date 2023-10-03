import numpy as np
import pandas as pd
import pytest

import tests.utils
from giskard import Dataset, Model
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
