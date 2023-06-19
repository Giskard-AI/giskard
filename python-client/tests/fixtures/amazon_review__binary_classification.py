import os
import string
from pathlib import Path

import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from nltk.stem.snowball import SnowballStemmer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import FunctionTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests.url_utils import fetch_from_ftp

# Constants.
RANDOM_SEED = 0
TEST_RATIO = 0.2

TARGET_THRESHOLD = 0.5

TARGET_COLUMN_NAME = "isHelpful"
FEATURE_COLUMN_NAME = "reviewText"

# Data.
DATA_URL = os.path.join("ftp://sys.giskard.ai", "pub", "unit_test_resources", "amazon_review_dataset", "reviews.json")
DATA_PATH = Path.home() / ".giskard" / "amazon_review_dataset" / "reviews.json"


def download_data(**kwargs) -> pd.DataFrame:
    fetch_from_ftp(DATA_URL, DATA_PATH)
    _df = pd.read_json(DATA_PATH, lines=True, **kwargs)
    return _df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    # Select columns.
    df = df[[FEATURE_COLUMN_NAME, "helpful"]]

    # Remove Null-characters (x00) from the dataset.
    df.reviewText = df.reviewText.apply(lambda x: x.replace("\x00", ""))

    # Extract numbers of helpful and total votes.
    df["helpful_ratings"] = df.helpful.apply(lambda x: x[0])
    df["total_ratings"] = df.helpful.apply(lambda x: x[1])

    # Filter unreasonable comments.
    df = df[df.total_ratings > 3]

    # Create target column.
    df[TARGET_COLUMN_NAME] = np.where((df.helpful_ratings / df.total_ratings) > TARGET_THRESHOLD, 1, 0).astype(int)

    # Delete columns we don't need anymore.
    df.drop(columns=["helpful", "helpful_ratings", "total_ratings"], inplace=True)
    return df


@pytest.fixture()
def amazon_review_data() -> Dataset:
    raw_data = preprocess_data(download_data(nrows=5000))
    wrapped_data = Dataset(
        raw_data, name="reviews", target=TARGET_COLUMN_NAME, column_types={FEATURE_COLUMN_NAME: "text"}
    )
    return wrapped_data


def make_lowercase(x):
    """Lower an input string."""
    x = x.reviewText.apply(lambda row: row.lower())
    return x


def remove_punctuation(x):
    """Remove punctuation from input string."""
    x.apply(lambda row: row.translate(str.maketrans("", "", string.punctuation)))
    return x


stemmer = SnowballStemmer("english")


def tokenizer(x):
    """Define string tokenization logic."""
    x = x.split()
    stems = list()
    [stems.append(stemmer.stem(word)) for word in x]
    return stems


@pytest.fixture()
def amazon_review_model(amazon_review_data: Dataset) -> SKLearnModel:
    x = amazon_review_data.df[[FEATURE_COLUMN_NAME]]
    y = amazon_review_data.df[TARGET_COLUMN_NAME]

    # Define and fit pipeline.
    vectorizer = TfidfVectorizer(tokenizer=tokenizer, stop_words="english", ngram_range=(1, 1), min_df=0.01)

    preprocessor = Pipeline(
        steps=[
            ("lowercase", FunctionTransformer(make_lowercase)),
            ("punctuation", FunctionTransformer(remove_punctuation)),
            ("vectorizer", vectorizer),
        ]
    )

    pipeline = Pipeline(
        steps=[("preprocessor", preprocessor), ("estimator", LogisticRegression(random_state=RANDOM_SEED))]
    )

    pipeline.fit(x, y)

    # Wrap pipeline.
    wrapped_model = SKLearnModel(
        model=pipeline,
        model_type="classification",
        feature_names=[FEATURE_COLUMN_NAME],
        name="review_helpfulness_predictor",
        classification_threshold=0.5,
        classification_labels=[0, 1],
    )

    return wrapped_model
