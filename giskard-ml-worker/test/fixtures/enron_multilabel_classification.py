import logging

import pandas as pd
import pytest
from sklearn import model_selection
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel
from giskard.ml_worker.utils.logging import Timer
from test import path

input_types = {
        "Subject": "text",
        "Content": "text",
        "Week_day": "category",
        "Month": "category",
        "Hour": "numeric",
        "Nb_of_forwarded_msg": "numeric",
        "Year": "numeric"
    }


@pytest.fixture()
def enron_data() -> GiskardDataset:
    logging.info("Fetching Enron Data")
    return GiskardDataset(
        df=pd.read_csv(path('test_data/enron_data.csv'),
                       keep_default_na=False,
                       na_values=["_GSK_NA_"]),
        target='Target',
        feature_types=input_types
    )


@pytest.fixture()
def enron_test_data(enron_data):
    return GiskardDataset(
        df=pd.DataFrame(enron_data.df).drop(columns=['Target']),
        feature_types=input_types,
        target=None
    )


@pytest.fixture()
def enron_model(enron_data) -> GiskardModel:
    timer = Timer()

    columns_to_scale = [key for key in input_types.keys() if input_types[key] == "numeric"]

    numeric_transformer = Pipeline([('imputer', SimpleImputer(strategy='median')),
                                    ('scaler', StandardScaler())])

    columns_to_encode = [key for key in input_types.keys() if input_types[key] == "category"]

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse=False))])

    text_transformer = Pipeline([
        ('vect', CountVectorizer()),
        ('tfidf', TfidfTransformer())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, columns_to_scale),
            ('cat', categorical_transformer, columns_to_encode),
            ('text_Mail', text_transformer, "Content")
        ]
    )
    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', LogisticRegression(max_iter=100))])

    Y = enron_data.df['Target']
    X = enron_data.df.drop(columns="Target")
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y,  # NOSONAR
                                                                        test_size=0.20,
                                                                        random_state=30,
                                                                        stratify=Y)
    clf.fit(X_train, Y_train)

    model_score = clf.score(X_test, Y_test)
    timer.stop(f"Trained model with score: {model_score}")

    return GiskardModel(
        prediction_function=clf.predict_proba,
        model_type='classification',
        feature_names=list(input_types),
        classification_threshold=0.5,
        classification_labels=clf.classes_
    )
