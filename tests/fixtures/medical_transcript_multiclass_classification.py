from typing import Iterable

import string
from pathlib import Path

import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests.url_utils import fetch_test_data

# Constants.
LABELS_LIST = [
    "Neurosurgery",
    "ENT - Otolaryngology",
    "Discharge Summary",
]

COLUMNS_DROP = ["Unnamed: 0", "description", "sample_name", "keywords"]

TEXT_COLUMN_NAME = "transcription"
TARGET_COLUMN_NAME = "medical_specialty"

LANGUAGE = "english"

# Paths.
DATA_URL = "https://giskard-library-test-datasets.s3.eu-north-1.amazonaws.com/medical_transcript_classification_dataset-mtsamples.csv.tar.gz"
DATA_PATH = Path.home() / ".giskard" / "medical_transcript_classification_dataset" / "mtsamples.csv.tar.gz"


def load_data() -> pd.DataFrame:
    # Download dataset.
    fetch_test_data(DATA_URL, DATA_PATH)
    df = pd.read_csv(DATA_PATH)

    # Drop useless columns.
    df = df.drop(columns=COLUMNS_DROP)

    # Trim text.
    df = df.apply(lambda x: x.str.strip())

    # Filter samples by label.
    df = df[df[TARGET_COLUMN_NAME].isin(LABELS_LIST)]

    # Sample data. We need to sample minimum samples > 100.
    examples_per_class = 34
    df = df.groupby(TARGET_COLUMN_NAME).apply(lambda x: x.sample(n=examples_per_class)).reset_index(drop=True)

    # Fill-in rows with no transcript by empty string.
    df = df.fillna(value={TEXT_COLUMN_NAME: ""})

    return df


@pytest.fixture(scope="session")
def medical_transcript_raw_data() -> Dataset:
    raw_data = load_data()
    return raw_data


@pytest.fixture()
def medical_transcript_data(medical_transcript_raw_data) -> Dataset:
    wrapped_data = Dataset(
        medical_transcript_raw_data,
        name="medical_transcript_dataset",
        target=TARGET_COLUMN_NAME,
        column_types={TEXT_COLUMN_NAME: "text"},
    )
    return wrapped_data


def preprocess_text(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess text."""

    # Remove punctuation.
    df[TEXT_COLUMN_NAME] = df[TEXT_COLUMN_NAME].apply(lambda x: x.translate(str.maketrans("", "", string.punctuation)))

    return df


def adapt_vectorizer_input(df: pd.DataFrame) -> Iterable:
    """Adapt input for the vectorizers.

    The problem is that vectorizers accept iterable, not DataFrame, but Series.
    Thus, we need to ravel dataframe with text have input single dimension.
    """

    df = df.iloc[:, 0]
    return df


@pytest.fixture(scope="session")
def medical_transcript_raw_model(medical_transcript_raw_data) -> SKLearnModel:
    # Define final pipeline.
    pipeline = Pipeline(
        steps=[
            ("text_preprocessor", FunctionTransformer(preprocess_text)),
            ("vectorizer_input_adapter", FunctionTransformer(adapt_vectorizer_input)),
            ("vectorizer", CountVectorizer(ngram_range=(1, 1))),
            ("estimator", RandomForestClassifier(n_estimators=10, max_depth=3, random_state=30)),
        ]
    )

    # Fit pipeline.
    pipeline.fit(medical_transcript_raw_data[[TEXT_COLUMN_NAME]], medical_transcript_raw_data[TARGET_COLUMN_NAME])

    return pipeline


@pytest.fixture()
def medical_transcript_model(medical_transcript_raw_model) -> SKLearnModel:
    # Wrap model with giskard
    wrapped_model = SKLearnModel(
        medical_transcript_raw_model,
        model_type="classification",
        name="medical_transcript_classification",
        feature_names=[TEXT_COLUMN_NAME],
        classification_labels=medical_transcript_raw_model.classes_,
    )

    return wrapped_model
