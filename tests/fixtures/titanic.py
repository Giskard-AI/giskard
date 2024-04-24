import pytest

from giskard import Dataset, Model
from giskard.demo import titanic


@pytest.fixture(scope="session")
def titanic_model_data_raw():
    return titanic()


@pytest.fixture()
def titanic_model(titanic_model_data_raw):
    return Model(
        titanic_model_data_raw[0],
        model_type="classification",
        name="Titanic binary classification model",
        description="The binary classification model, which predicts, whether the passenger survived or not in the Titanic incident. \n"
        "The model outputs yes, if the person survived, and no - if he died.",
    )


@pytest.fixture()
def titanic_dataset(titanic_model_data_raw):
    return Dataset(
        titanic_model_data_raw[1],
        target="Survived",
        name="Titanic dataset",
        cat_columns=["Pclass", "Sex", "SibSp", "Parch", "Embarked"],
    )
