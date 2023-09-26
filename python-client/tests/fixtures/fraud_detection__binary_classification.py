from pathlib import Path

import pandas as pd
import pytest
from pandas.api.types import union_categoricals
from sklearn.model_selection import train_test_split

from giskard import Dataset, Model
from tests.url_utils import fetch_from_ftp

# Data.
DATA_URL = "ftp://sys.giskard.ai/pub/unit_test_resources/fraud_detection_classification_dataset/{}"
DATA_PATH = Path.home() / ".giskard" / "fraud_detection_classification_dataset"

# Constants.
TARGET_COLUMN = "isTest"
IDX_LABEL = "TransactionID"

# Define data-types of transactions features.
DATA_TYPES_TRANSACTION = {
    "TransactionID": "int32",
    "isFraud": "int8",
    "TransactionDT": "int32",
    "TransactionAmt": "float32",
    "ProductCD": "category",
    "card1": "int16",
    "card2": "float32",
    "card3": "float32",
    "card4": "category",
    "card5": "float32",
    "card6": "category",
    "addr1": "float32",
    "addr2": "float32",
    "dist1": "float32",
    "dist2": "float32",
    "P_emaildomain": "category",
    "R_emaildomain": "category",
}

C_COLS = [f"C{i}" for i in range(1, 15)]
D_COLS = [f"D{i}" for i in range(1, 16)]
M_COLS = [f"M{i}" for i in range(1, 10)]
V_COLS = [f"V{i}" for i in range(1, 340)]

DATA_TYPES_TRANSACTION.update((c, "float32") for c in C_COLS)
DATA_TYPES_TRANSACTION.update((c, "float32") for c in D_COLS)
DATA_TYPES_TRANSACTION.update((c, "float32") for c in V_COLS)
DATA_TYPES_TRANSACTION.update((c, "category") for c in M_COLS)

# Define datatypes of identity features.
DATA_TYPES_ID = {
    "TransactionID": "int32",
    "DeviceType": "category",
    "DeviceInfo": "category",
}

ID_COLS = [f"id_{i:02d}" for i in range(1, 39)]
ID_CATS = [
    "id_12",
    "id_15",
    "id_16",
    "id_23",
    "id_27",
    "id_28",
    "id_29",
    "id_30",
    "id_31",
    "id_33",
    "id_34",
    "id_35",
    "id_36",
    "id_37",
    "id_38",
]

DATA_TYPES_ID.update(((c, "float32") for c in ID_COLS))
DATA_TYPES_ID.update(((c, "category") for c in ID_CATS))

# Define list of all categorical features.
CATEGORICALS = [
    f_name for (f_name, f_type) in dict(DATA_TYPES_TRANSACTION, **DATA_TYPES_ID).items() if f_type == "category"
]


def fetch_dataset():
    files_to_fetch = ["train_transaction.csv", "train_identity.csv", "test_transaction.csv", "test_identity.csv"]
    for file_name in files_to_fetch:
        fetch_from_ftp(DATA_URL.format(file_name), DATA_PATH / file_name)


def read_set(_type, nrows=150):
    """Read both transactions and identity data."""
    fetch_dataset()

    _df = pd.read_csv(
        DATA_PATH / f"{_type}_transaction.csv", index_col=IDX_LABEL, dtype=DATA_TYPES_TRANSACTION, nrows=nrows
    )
    _df = _df.join(pd.read_csv(DATA_PATH / f"{_type}_identity.csv", index_col=IDX_LABEL, dtype=DATA_TYPES_ID))

    return _df


def read_dataset():
    """Read whole data."""
    train_set = read_set("train")
    test_set = read_set("test")
    return train_set, test_set


def preprocess_dataset(train_set, test_set):
    """Unite train and test into common dataframe."""
    # Create a new target column and remove a former one from the train data.
    train_set.pop("isFraud")
    train_set["isTest"] = 0
    test_set["isTest"] = 1

    # Preprocess categorical features.
    n_train = train_set.shape[0]
    for c in train_set.columns:
        s = train_set[c]
        if hasattr(s, "cat"):
            u = union_categoricals([train_set[c], test_set[c]], sort_categories=True)
            train_set[c] = u[:n_train]
            test_set[c] = u[n_train:]

    # Unite train and test data.
    united = pd.concat([train_set, test_set])

    # Add additional features.
    united["TimeInDay"] = united.TransactionDT % 86400
    united["Cents"] = united.TransactionAmt % 1

    # Remove useless columns.
    united.drop("TransactionDT", axis=1, inplace=True)

    # Split in train/test sets
    train_set, test_set = train_test_split(united, test_size=0.5, random_state=41)

    return train_set, test_set


@pytest.fixture()
def fraud_detection_data() -> Dataset:
    _, test_set = preprocess_dataset(*read_dataset())
    wrapped_dataset = Dataset(
        test_set, name="fraud_detection_adversarial_dataset", target=TARGET_COLUMN, cat_columns=CATEGORICALS
    )
    return wrapped_dataset


@pytest.fixture(scope="session")
def fraud_detection_train_data() -> Dataset:
    train_set, _ = preprocess_dataset(*read_dataset())
    wrapped_dataset = Dataset(
        train_set, name="fraud_detection_adversarial_dataset", target=TARGET_COLUMN, cat_columns=CATEGORICALS
    )
    return wrapped_dataset


@pytest.fixture(scope="session")
def fraud_detection_model(fraud_detection_train_data: Dataset) -> Model:
    from lightgbm import LGBMClassifier

    x = fraud_detection_train_data.df.drop(TARGET_COLUMN, axis=1)
    y = fraud_detection_train_data.df[TARGET_COLUMN]

    estimator = LGBMClassifier(random_state=30)
    estimator.fit(x, y)

    wrapped_model = Model(
        estimator,
        model_type="classification",
        name="train_test_data_classifier",
        feature_names=x.columns,
        classification_threshold=0.5,
        classification_labels=[0, 1],
    )

    return wrapped_model
