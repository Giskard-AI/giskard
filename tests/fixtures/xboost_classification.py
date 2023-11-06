import logging

import pandas as pd
import pytest
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from giskard import Model
from giskard.datasets.base import Dataset

logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
TARGET_COLUMN_NAME = "target"


@pytest.fixture(scope="session")
def breast_cancer_raw_data() -> Dataset:
    logger.info("Fetching Breast Cancer Data")
    raw_data = load_breast_cancer(as_frame=True)
    df = pd.concat([raw_data.data, raw_data.target], axis=1)
    return df


@pytest.fixture()
def breast_cancer_data(breast_cancer_raw_data) -> Dataset:
    return Dataset(
        breast_cancer_raw_data,
        name="breast_cancer",
        target="target",
        column_types={col: "numeric" for col in breast_cancer_raw_data.columns},
    )


@pytest.fixture(scope="session")
def breast_cancer_row_model(breast_cancer_raw_data) -> Model:
    X_train, X_test, y_train, y_test = train_test_split(
        breast_cancer_raw_data.loc[:, breast_cancer_raw_data.columns != TARGET_COLUMN_NAME],
        breast_cancer_raw_data[TARGET_COLUMN_NAME],
        random_state=RANDOM_SEED,
    )
    xgb = XGBClassifier(objective="binary:logistic", random_state=30)
    xgb.fit(X_train, y_train)
    return xgb, X_test.columns.tolist()


@pytest.fixture()
def breast_cancer_model(breast_cancer_row_model) -> Model:
    model, features = breast_cancer_row_model
    return Model(
        model=model,
        model_type="classification",
        feature_names=features,
        name="breast_cancer_xgboost",
        classification_threshold=0.5,
        classification_labels=[0, 1],
    )
