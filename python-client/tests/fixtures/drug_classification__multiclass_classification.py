from pathlib import Path

import pytest
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import OneHotEncoder
from imblearn.pipeline import Pipeline as PipelineImb

from giskard import Dataset
from giskard.models.sklearn import SKLearnModel
from tests.url_utils import fetch_from_ftp


# Data.
DATA_URL = '/'.join(
    ["ftp://sys.giskard.ai", "pub", "unit_test_resources", "drug_classification_dataset", "drug200.csv"]
)
DATA_PATH = Path.home() / ".giskard" / "drug_classification_dataset" / "drug200.csv"

# Constants.
TARGET_NAME = "Drug"

AGE_BINS = [0, 19, 29, 39, 49, 59, 69, 80]
AGE_CATEGORIES = ["<20s", "20s", "30s", "40s", "50s", "60s", ">60s"]

NA_TO_K_BINS = [0, 9, 19, 29, 50]
NA_TO_K_CATEGORIES = ["<10", "10-20", "20-30", ">30"]


def bin_numerical(df: pd.DataFrame) -> np.ndarray:
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


@pytest.fixture()
def drug_classification_data() -> Dataset:
    # Download data.
    fetch_from_ftp(DATA_URL, DATA_PATH)

    # Load and wrap data.
    raw_data = bin_numerical(pd.read_csv(DATA_PATH))
    wrapped_dataset = Dataset(
        raw_data,
        name="drug_classification_dataset",
        target=TARGET_NAME,
        cat_columns=raw_data.drop(columns=[TARGET_NAME]).columns.tolist(),
    )
    return wrapped_dataset


@pytest.fixture()
def drug_classification_model(drug_classification_data) -> SKLearnModel:
    x = drug_classification_data.df.drop(TARGET_NAME, axis=1)
    y = drug_classification_data.df.Drug

    pipeline = PipelineImb(
        steps=[
            ("one_hot_encoder", OneHotEncoder()),
            ("resampler", SMOTE()),
            ("classifier", SVC(kernel="linear", max_iter=250, probability=True)),
        ]
    )

    pipeline.fit(x, y)

    wrapped_model = SKLearnModel(
        pipeline, model_type="classification", name="drug_classifier", feature_names=x.columns.tolist()
    )
    return wrapped_model
