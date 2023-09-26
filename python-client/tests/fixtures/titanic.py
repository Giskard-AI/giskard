import pytest

from giskard import Model, Dataset
from giskard.demo import titanic


@pytest.fixture(scope="session")
def titanic_model_data_raw():
    return titanic()


@pytest.fixture()
def titanic_model(titanic_model_data_raw):
    return Model(titanic_model_data_raw[0], model_type="classification", name="Titanic model")


@pytest.fixture()
def titanic_dataset(titanic_model_data_raw):
    return Dataset(titanic_model_data_raw[1], target="Survived", name="Titanic dataset")
