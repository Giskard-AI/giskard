import pandas as pd
from sklearn import model_selection
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer


def titanic():
    df = pd.read_csv("https://raw.githubusercontent.com/Giskard-AI/giskard-examples/main/datasets/titanic_train.csv")
    df.drop(["Ticket", "Cabin"], axis=1, inplace=True)
    cat_cols = ['Pclass', 'Sex', "SibSp", "Parch", "Embarked"]
    num_cols = ["PassengerId", "Age", "Fare"]
    text_cols = ["Name"]
    target = "Survived"

    # tfidf the text column
    text_transformer = Pipeline([('tfidf', TfidfVectorizer(lowercase=False, strip_accents=None))])

    # transform and scale the numeric columns
    num_transformer = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])

    # one hot encode the categorical values
    cat_transormer = Pipeline([('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                               ('onehot', OneHotEncoder(handle_unknown='ignore',
                                                        sparse=False))])

    # Perform preprocessing of the columns with the above pipelines
    preprocessor = ColumnTransformer(
        transformers=[('text', text_transformer, text_cols[0]),
                      ('num', num_transformer, num_cols),
                      ('cat', cat_transormer, cat_cols)])

    # Pipeline for the model Logistic Regression
    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', LogisticRegression())])

    Y = df[target]
    X = df.drop(target, axis=1)
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y, test_size=0.50, random_state=30,
                                                                        stratify=Y)

    clf.fit(X_train, Y_train)

    test_data = pd.concat([X_test, Y_test], axis=1)

    return clf, test_data
