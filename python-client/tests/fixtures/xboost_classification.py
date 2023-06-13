import logging

import pandas as pd
import pytest
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from giskard.datasets.base import Dataset
from giskard import Model

logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
TARGET_COLUMN_NAME = "target"


@pytest.fixture()
def breast_cancer_data() -> Dataset:
    logger.info("Fetching Breast Cancer Data")
    raw_data = load_breast_cancer(as_frame=True)
    df = pd.concat([raw_data.data, raw_data.target], axis=1)
    column_types = {col: "numeric" for col in raw_data.data.columns}
    return Dataset(df, name="breast_cancer", target="target", column_types=column_types)


@pytest.fixture()
def breast_cancer_model(breast_cancer_data: Dataset) -> Model:
    X_train, X_test, y_train, y_test = train_test_split(
        breast_cancer_data.df.loc[:, breast_cancer_data.df.columns != TARGET_COLUMN_NAME],
        breast_cancer_data.df[TARGET_COLUMN_NAME],
        random_state=RANDOM_SEED,
    )
    xgb = XGBClassifier(objective="binary:logistic")
    xgb.fit(X_train, y_train)
    return Model(
        model=xgb,
        model_type="classification",
        feature_names=X_test.columns,
        name="breast_cancer_xgboost",
        classification_threshold=0.5,
        classification_labels=[0, 1],
    )
