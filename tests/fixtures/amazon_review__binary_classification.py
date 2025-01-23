import string

import numpy as np
import pandas as pd
import pytest
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests import path

# Constants.
RANDOM_SEED = 0
TEST_RATIO = 0.2

TARGET_THRESHOLD = 0.5

TARGET_COLUMN_NAME = "isHelpful"
FEATURE_COLUMN_NAME = "reviewText"

# Data.
DATA_PATH = path("test_data/amazon_reviews.json.tar.gz")


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


@pytest.fixture(scope="session")
def amazon_review_raw_data() -> pd.DataFrame:
    return preprocess_data(pd.read_json(DATA_PATH, lines=True, nrows=5000))


@pytest.fixture()
def amazon_review_data(amazon_review_raw_data: pd.DataFrame) -> Dataset:
    return Dataset(
        amazon_review_raw_data, name="reviews", target=TARGET_COLUMN_NAME, column_types={FEATURE_COLUMN_NAME: "text"}
    )


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


@pytest.fixture(scope="session")
def amazon_review_raw_model(amazon_review_raw_data: pd.DataFrame) -> Pipeline:
    x = amazon_review_raw_data[[FEATURE_COLUMN_NAME]]
    y = amazon_review_raw_data[TARGET_COLUMN_NAME]

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
    return pipeline


@pytest.fixture()
def amazon_review_model(amazon_review_raw_model) -> SKLearnModel:
    # Wrap pipeline.
    wrapped_model = SKLearnModel(
        model=amazon_review_raw_model,
        model_type="classification",
        feature_names=[FEATURE_COLUMN_NAME],
        name="review_helpfulness_predictor",
        classification_threshold=0.5,
        classification_labels=[0, 1],
    )

    return wrapped_model
