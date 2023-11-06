from typing import List, Tuple

from pathlib import Path

import pandas as pd
import pytest
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as PipelineImb
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import SVC

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests.url_utils import fetch_from_ftp

# Data.
DATA_URL = "ftp://sys.giskard.ai/pub/unit_test_resources/drug_classification_dataset/drug200.csv"
DATA_PATH = Path.home() / ".giskard" / "drug_classification_dataset" / "drug200.csv"

# Constants.
TARGET_NAME = "Drug"

AGE_BINS = [0, 19, 29, 39, 49, 59, 69, 80]
AGE_CATEGORIES = ["<20s", "20s", "30s", "40s", "50s", "60s", ">60s"]

NA_TO_K_BINS = [0, 9, 19, 29, 50]
NA_TO_K_CATEGORIES = ["<10", "10-20", "20-30", ">30"]


def bin_numerical(df: pd.DataFrame) -> pd.DataFrame:
    """Perform numerical features binning."""

    def _bin_age(_df: pd.DataFrame) -> pd.DataFrame:
        """Bin age feature."""
        _df.Age = pd.cut(_df.Age, bins=AGE_BINS, labels=AGE_CATEGORIES)
        return _df

    def _bin_na_to_k(_df: pd.DataFrame) -> pd.DataFrame:
        """Bin Na_to_K feature."""
        _df.Na_to_K = pd.cut(_df.Na_to_K, bins=NA_TO_K_BINS, labels=NA_TO_K_CATEGORIES)
        return _df

    df = df.copy()
    df = _bin_age(df)
    df = _bin_na_to_k(df)

    return df


@pytest.fixture(scope="session")
def drug_classification_raw_data() -> pd.DataFrame:
    # Download data.
    fetch_from_ftp(DATA_URL, DATA_PATH)

    # Load and wrap data.
    raw_data = bin_numerical(pd.read_csv(DATA_PATH))
    return raw_data


@pytest.fixture()
def drug_classification_data(drug_classification_raw_data: pd.DataFrame) -> Dataset:
    wrapped_dataset = Dataset(
        drug_classification_raw_data,
        name="drug_classification_dataset",
        target=TARGET_NAME,
        cat_columns=drug_classification_raw_data.drop(columns=[TARGET_NAME]).columns.tolist(),
    )
    return wrapped_dataset


@pytest.fixture(scope="session")
def drug_classification_raw_model(drug_classification_raw_data: pd.DataFrame) -> Tuple[PipelineImb, List[str]]:
    x = drug_classification_raw_data.drop(TARGET_NAME, axis=1)
    y = drug_classification_raw_data[TARGET_NAME]

    pipeline = PipelineImb(
        steps=[
            ("one_hot_encoder", OneHotEncoder()),
            ("resampler", SMOTE()),
            ("classifier", SVC(random_state=30, kernel="linear", max_iter=250, probability=True)),
        ]
    )

    pipeline.fit(x, y)
    return pipeline, x.columns.to_list()


@pytest.fixture()
def drug_classification_model(drug_classification_raw_model: Tuple[PipelineImb, List[str]]) -> SKLearnModel:
    model, features = drug_classification_raw_model
    return SKLearnModel(
        model,
        model_type="classification",
        name="drug_classifier",
        feature_names=features,
    )
