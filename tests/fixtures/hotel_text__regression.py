from typing import Iterable

from pathlib import Path

import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests.url_utils import fetch_test_data

# Data.
DATA_URL = "https://giskard-library-test-datasets.s3.eu-north-1.amazonaws.com/hotel_text_regression_dataset-Hotel_Reviews.csv.tar.gz"
DATA_PATH = Path.home() / ".giskard" / "hotel_text_regression_dataset" / "Hotel_Reviews.csv.tar.gz"

# Constants.
FEATURE_COLUMN_NAME = "Full_Review"
TARGET_COLUMN_NAME = "Reviewer_Score"


def load_data(**kwargs) -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, **kwargs)

    # Create target column.
    df[FEATURE_COLUMN_NAME] = df.apply(lambda x: x["Positive_Review"] + " " + x["Negative_Review"], axis=1)

    return df


@pytest.fixture(scope="session")
def hotel_text_raw_data():
    fetch_test_data(DATA_URL, DATA_PATH)

    raw_data = load_data(nrows=105)[[FEATURE_COLUMN_NAME, TARGET_COLUMN_NAME]]
    return raw_data


@pytest.fixture()
def hotel_text_data(hotel_text_raw_data) -> Dataset:
    wrapped_data = Dataset(
        hotel_text_raw_data,
        name="hotel_text_regression_dataset",
        target=TARGET_COLUMN_NAME,
        column_types={FEATURE_COLUMN_NAME: "text"},
    )
    return wrapped_data


def adapt_vectorizer_input(df: pd.DataFrame) -> Iterable:
    """Adapt input for the vectorizers.

    The problem is that vectorizers accept iterable, not DataFrame, but Series.
    Thus, we need to ravel dataframe with text have input single dimension.
    """

    df = df.iloc[:, 0]
    return df


@pytest.fixture(scope="session")
def hotel_text_raw_model(hotel_text_raw_data) -> SKLearnModel:
    x = hotel_text_raw_data[[FEATURE_COLUMN_NAME]]
    y = hotel_text_raw_data[TARGET_COLUMN_NAME]

    pipeline = Pipeline(
        steps=[
            ("vectorizer_adapter", FunctionTransformer(adapt_vectorizer_input)),
            ("vectorizer", TfidfVectorizer(max_features=10000)),
            ("regressor", GradientBoostingRegressor(random_state=30, n_estimators=5)),
        ]
    )

    pipeline.fit(x, y)
    return pipeline


@pytest.fixture()
def hotel_text_model(hotel_text_raw_model) -> SKLearnModel:
    wrapped_model = SKLearnModel(
        hotel_text_raw_model,
        model_type="regression",
        name="hotel_text_regression",
        feature_names=[FEATURE_COLUMN_NAME],
        description="The linear regression model, which predict hotel review's score based on its contents. The worst score is 0 and the best is 10.",
    )

    return wrapped_model
