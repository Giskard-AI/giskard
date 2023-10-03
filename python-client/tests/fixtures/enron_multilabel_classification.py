import email
import logging
from collections import defaultdict

import pandas as pd
import pytest
from dateutil import parser
from sklearn import model_selection
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.ml_worker.utils.logging import Timer
from giskard.models.sklearn import SKLearnModel
from tests import path
from tests.utils import get_email_files

logger = logging.getLogger(__name__)

LABEL_CAT = 3


idx_to_cat = {
    1: "REGULATION",
    2: "INTERNAL",
    3: "INFLUENCE",
    4: "INFLUENCE",
    5: "INFLUENCE",
    6: "CALIFORNIA CRISIS",
    7: "INTERNAL",
    8: "INTERNAL",
    9: "INFLUENCE",
    10: "REGULATION",
    11: "talking points",
    12: "meeting minutes",
    13: "trip reports",
}

input_types = {
    "Subject": "text",
    "Content": "text",
    "Week_day": "category",
    "Month": "category",
    "Hour": "numeric",
    "Nb_of_forwarded_msg": "numeric",
    "Year": "numeric",
}


# get_labels returns a dictionary representation of these labels.
def get_labels(filename):
    with open(filename + ".cats") as f:
        labels = defaultdict(dict)
        line = f.readline()
        while line:
            line = line.split(",")
            top_cat, sub_cat, freq = int(line[0]), int(line[1]), int(line[2])
            labels[top_cat][sub_cat] = freq
            line = f.readline()
    return dict(labels)


@pytest.fixture()
def enron_data() -> Dataset:
    logger.info("Fetching Enron Data")
    df = pd.read_csv(path("test_data/enron_data.csv"), keep_default_na=False, na_values=["_GSK_NA_"])
    df.drop(columns="Unnamed: 0", inplace=True)
    return Dataset(df=df, target="Target", column_types=input_types)


@pytest.fixture()
def enron_data_full() -> Dataset:
    logger.info("Fetching Enron Data")
    email_files = get_email_files()

    columns_name = ["Target", "Subject", "Content", "Week_day", "Year", "Month", "Hour", "Nb_of_forwarded_msg"]

    data_list = []
    for email_file in email_files:
        values_to_add = {}

        # Target is the sub-category with maximum frequency
        if LABEL_CAT in get_labels(email_file):
            sub_cat_dict = get_labels(email_file)[LABEL_CAT]
            target_int = max(sub_cat_dict, key=sub_cat_dict.get)
            values_to_add["Target"] = str(idx_to_cat[target_int])

        # Features are metadata from the email object
        filename = email_file + ".txt"
        with open(filename) as f:
            message = email.message_from_string(f.read())

            values_to_add["Subject"] = str(message["Subject"])
            values_to_add["Content"] = str(message.get_payload())

            date_time_obj = parser.parse(message["Date"])
            values_to_add["Week_day"] = date_time_obj.strftime("%A")
            values_to_add["Year"] = date_time_obj.strftime("%Y")
            values_to_add["Month"] = date_time_obj.strftime("%B")
            values_to_add["Hour"] = int(date_time_obj.strftime("%H"))

            # Count number of forwarded mails
            number_of_messages = 0
            for line in message.get_payload().split("\n"):
                if ("forwarded" in line.lower() or "original" in line.lower()) and "--" in line:
                    number_of_messages += 1
            values_to_add["Nb_of_forwarded_msg"] = number_of_messages

        data_list.append(values_to_add)

    data = pd.DataFrame(data_list, columns=columns_name)

    # We filter 879 rows (if Primary topics exists (i.e. if coarse genre 1.1 is selected) )
    data_filtered = data[data["Target"].notnull()]
    data_filtered = data_filtered.head(150)  # Sample to make the scan faster
    data_filtered.Year = data_filtered.Year.astype(float)
    return Dataset(df=data_filtered, target="Target", cat_columns=["Week_day", "Month"])


@pytest.fixture()
def enron_test_data(enron_data):
    return Dataset(df=pd.DataFrame(enron_data.df).drop(columns=["Target"]), target=None, column_types=input_types)


@pytest.fixture()
def enron_model(enron_data) -> SKLearnModel:
    timer = Timer()

    columns_to_scale = [key for key in input_types.keys() if input_types[key] == "numeric"]

    numeric_transformer = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])

    columns_to_encode = [key for key in input_types.keys() if input_types[key] == "category"]

    categorical_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse=False)),
        ]
    )

    text_transformer = Pipeline([("vect", CountVectorizer()), ("tfidf", TfidfTransformer())])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, columns_to_scale),
            ("cat", categorical_transformer, columns_to_encode),
            ("text_Mail", text_transformer, "Content"),
        ]
    )
    clf = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", LogisticRegression(max_iter=100, random_state=30))])

    Y = enron_data.df["Target"]
    X = enron_data.df.drop(columns="Target")
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(
        X, Y, test_size=0.20, random_state=30, stratify=Y  # NOSONAR
    )
    clf.fit(X_train, Y_train)

    model_score = clf.score(X_test, Y_test)
    timer.stop(f"Trained model with score: {model_score}")

    return SKLearnModel(
        model=clf,
        model_type=SupportedModelTypes.CLASSIFICATION,
        feature_names=list(input_types),
        classification_threshold=0.5,
    )
