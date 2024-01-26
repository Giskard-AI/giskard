from typing import Any, Tuple

import os
from enum import Enum

import pandas as pd


class ModelTypes(str, Enum):
    LOGISTIC_REGRESSION = "LogisticRegression"
    LGBM_CLASSIFIER = "LGBMClassifier"


def get_df():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "titanic.csv"))
    df.drop(["Ticket", "Cabin"], axis=1, inplace=True)
    _classification_labels = {0: "no", 1: "yes"}
    df["Survived"] = df["Survived"].apply(lambda x: _classification_labels[x])
    return df


def get_test_df():
    from sklearn import model_selection

    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "titanic.csv"))
    df.drop(["Ticket", "Cabin"], axis=1, inplace=True)
    _classification_labels = {0: "no", 1: "yes"}
    df["Survived"] = df["Survived"].apply(lambda x: _classification_labels[x])
    Y = df["Survived"]
    X = df.drop("Survived", axis=1)
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(
        X, Y, test_size=0.50, random_state=30, stratify=Y
    )
    test_df = pd.concat([X_test, Y_test], axis=1)
    return test_df


def get_model_and_df(model: str = ModelTypes.LOGISTIC_REGRESSION, max_iter: int = 100) -> Tuple[Any, pd.DataFrame]:
    from sklearn import model_selection
    from sklearn.compose import ColumnTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    df = get_df()
    cat_cols = ["Pclass", "Sex", "SibSp", "Parch", "Embarked"]
    num_cols = ["PassengerId", "Age", "Fare"]
    text_cols = ["Name"]
    target = "Survived"

    # tfidf the text column
    text_transformer = Pipeline([("tfidf", TfidfVectorizer(lowercase=False, strip_accents=None))])

    # transform and scale the numeric columns
    num_transformer = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])

    # one hot encode the categorical values
    cat_transormer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    # Perform preprocessing of the columns with the above pipelines
    preprocessor = ColumnTransformer(
        transformers=[
            ("text", text_transformer, text_cols[0]),
            ("num", num_transformer, num_cols),
            ("cat", cat_transormer, cat_cols),
        ]
    )

    # Define the final ML Pipeline.
    if model.lower() == ModelTypes.LOGISTIC_REGRESSION.lower():
        clf = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", LogisticRegression(max_iter=max_iter))])
    elif model.lower() == ModelTypes.LGBM_CLASSIFIER.lower():
        from lightgbm import LGBMClassifier

        clf = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", LGBMClassifier(n_estimators=max_iter))])
    else:
        raise NotImplementedError(f"The model type '{model}' is not supported!")

    Y = df[target]
    X = df.drop(target, axis=1)
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(
        X, Y, test_size=0.50, random_state=30, stratify=Y
    )

    clf.fit(X_train, Y_train)

    test_data = pd.concat([X_test, Y_test], axis=1)

    return clf, test_data


def get_pipeline():
    clf, _ = get_model_and_df()

    def preprocessor(df):
        return clf[0].transform(df)

    return preprocessor, clf[1]
