import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from giskard.models.catboost import CatboostModel
from tests.utils import verify_model_upload


def test_catboost_model_save_and_upload(german_credit_catboost, german_credit_data):
    assert isinstance(german_credit_catboost, CatboostModel)
    verify_model_upload(german_credit_catboost, german_credit_data)


def test_catboost_model_detects_feature_names():
    df = pd.DataFrame({"feature_1": np.random.normal(size=100), "feature_2": ["cat1"] * 10 + ["cat2"] * 90})
    classifier = CatBoostClassifier(cat_features=["feature_2"])
    classifier.fit(df, ["target1"] * 90 + ["target2"] * 10)

    model = CatboostModel(
        model=classifier,
        model_type="classification",
        feature_names=None,  # we are not passing feature names here
        classification_labels=None,  # we are not passing labels here
    )

    assert model.meta.feature_names == ["feature_1", "feature_2"]
    assert model.meta.classification_labels == ["target1", "target2"]
