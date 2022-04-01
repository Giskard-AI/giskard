import logging
from logging.config import fileConfig
from pathlib import Path

import pandas as pd
import pytest
import time
from sklearn import model_selection
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

fileConfig('../logging_config.ini')


@pytest.fixture()
def german_credit_data():
    logging.info("Reading german_credit_prepared.csv")
    return pd.read_csv(Path('test_data', 'german_credit_prepared.csv'))


@pytest.fixture()
def german_credit_test_data(german_credit_data):
    return pd.DataFrame(german_credit_data).drop(columns=['default'])


@pytest.fixture()
def german_credit_model(german_credit_data):
    logging.info('Training German credit scoring classification model')
    start = time.time()

    input_types = {'account_check_status': "category",
                   'duration_in_month': "numeric",
                   'credit_history': "category",
                   'purpose': "category",
                   'credit_amount': "numeric",
                   'savings': "category",
                   'present_emp_since': "category",
                   'installment_as_income_perc': "numeric",
                   'sex': "category",
                   'personal_status': "category",
                   'other_debtors': "category",
                   'present_res_since': "numeric",
                   'property': "category",
                   'age': "numeric",
                   'other_installment_plans': "category",
                   'housing': "category",
                   'credits_this_bank': "numeric",
                   'job': "category",
                   'people_under_maintenance': "numeric",
                   'telephone': "category",
                   'foreign_worker': "category"}
    columns_to_scale = [key for key in input_types.keys() if input_types[key] == "numeric"]

    numeric_transformer = Pipeline([('imputer', SimpleImputer(strategy='median')),
                                    ('scaler', StandardScaler())])

    columns_to_encode = [key for key in input_types.keys() if input_types[key] == "category"]

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse=False))])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, columns_to_scale),
            ('cat', categorical_transformer, columns_to_encode)
        ]
    )
    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', LogisticRegression(max_iter=100))])

    Y = german_credit_data['default']
    X = german_credit_data.drop(columns="default")
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y,
                                                                        test_size=0.20,
                                                                        random_state=30,
                                                                        stratify=Y)
    clf.fit(X_train, Y_train)

    train_time = time.time() - start
    model_score = clf.score(X_test, Y_test)
    logging.info(f"Trained model with score: {model_score} in {round(train_time * 1000)} ms")
    return clf.predict_proba
