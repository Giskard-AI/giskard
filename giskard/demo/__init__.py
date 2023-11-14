from . import linear_regression, titanic_classification


def titanic_df():
    return titanic_classification.get_test_df()


def titanic(model="LogisticRegression", max_iter=100):
    return titanic_classification.get_model_and_df(model=model, max_iter=max_iter)


def titanic_pipeline():
    return titanic_classification.get_pipeline()


def linear_df():
    return linear_regression.get_df()


def linear():
    return linear_regression.get_model_and_df()


def linear_pipeline():
    return linear_regression.get_pipeline()


__all__ = [
    "titanic_df",
    "titanic",
    "titanic_pipeline",
    "linear_df",
    "linear",
    "linear_pipeline",
]
