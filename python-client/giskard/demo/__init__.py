import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

def titanic():
    df = pd.read_csv("https://raw.githubusercontent.com/Giskard-AI/giskard-examples/main/datasets/titanic_train.csv")
    df.dropna(inplace=True)
    df.drop(["Ticket", "Cabin"], axis=1, inplace=True)
    cat_cols=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"]
    num_cols=["PassengerId", "Age", "Fare"]
    text_cols=["Name"]
    target = "Survived"

    # tfidf the text column
    text_transformer = Pipeline([('tfidf', TfidfVectorizer(lowercase=False, strip_accents=None))])

    # transform and scale the numeric columns
    num_transformer = Pipeline([('scaler', StandardScaler())])

    # one hot encode the categorical values
    cat_transormer = Pipeline([('onehot', OneHotEncoder(handle_unknown='ignore',
                                                        sparse=False))])

    # Perform preprocessing of the columns with the above pipelines
    preprocessor = ColumnTransformer(
        transformers=[('text', text_transformer, text_cols[0]),
                      ('num', num_transformer, num_cols),
                      ('cat', cat_transormer, cat_cols)])

    # Pipeline for the model Logistic Regression
    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', LogisticRegression())])

    y = df[target]
    X = df.drop(target, axis=1)
    clf.fit(X, y)
    print("accuracy = ", round(clf.score(X, y) * 100, 2), "%")

    return clf, df
