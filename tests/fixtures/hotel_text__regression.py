from pathlib import Path
from typing import Iterable

import pytest
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer

from giskard import Dataset
from tests.url_utils import fetch_from_ftp
from giskard.models.sklearn import SKLearnModel


# Data.
DATA_URL = "ftp://sys.giskard.ai/pub/unit_test_resources/hotel_text_regression_dataset/Hotel_Reviews.csv"
DATA_PATH = Path.home() / ".giskard" / "hotel_text_regression_dataset" / "Hotel_Reviews.csv"

# Constants.
FEATURE_COLUMN_NAME = "Full_Review"
TARGET_COLUMN_NAME = "Reviewer_Score"


def load_data(**kwargs) -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, **kwargs)

    # Create target column.
    df[FEATURE_COLUMN_NAME] = df.apply(lambda x: x["Positive_Review"] + " " + x["Negative_Review"], axis=1)

    return df


@pytest.fixture
def hotel_text_data() -> Dataset:
    fetch_from_ftp(DATA_URL, DATA_PATH)

    raw_data = load_data(nrows=105)[[FEATURE_COLUMN_NAME, TARGET_COLUMN_NAME]]
    wrapped_data = Dataset(
        raw_data,
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


@pytest.fixture
def hotel_text_model(hotel_text_data) -> SKLearnModel:
    x = hotel_text_data.df[[FEATURE_COLUMN_NAME]]
    y = hotel_text_data.df[TARGET_COLUMN_NAME]

    pipeline = Pipeline(
        steps=[
            ("vectorizer_adapter", FunctionTransformer(adapt_vectorizer_input)),
            ("vectorizer", TfidfVectorizer(max_features=10000)),
            ("regressor", GradientBoostingRegressor(random_state=30, n_estimators=5)),
        ]
    )

    pipeline.fit(x, y)

    wrapped_model = SKLearnModel(
        pipeline, model_type="regression", name="hotel_text_regression", feature_names=[FEATURE_COLUMN_NAME]
    )

    return wrapped_model
