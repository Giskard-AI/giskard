import pytest
from pandas import DataFrame
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.models.sklearn import SKLearnModel
from giskard.utils.logging import Timer


@pytest.fixture(scope="session")
def linear_regression_diabetes_raw(diabetes_raw_dataset: DataFrame):
    timer = Timer()

    diabetes_x = diabetes_raw_dataset.drop(columns=["target"])
    diabetes_y = diabetes_raw_dataset["target"]

    # Split the data into training/testing sets
    diabetes_x_train = diabetes_x[:-20]
    diabetes_x_test = diabetes_x[-20:]

    # Split the targets into training/testing sets
    diabetes_y_train = diabetes_y[:-20]
    diabetes_y_test = diabetes_y[-20:]

    # Create linear regression object
    regressor = linear_model.LinearRegression()

    # Train the model using the training sets
    regressor.fit(diabetes_x_train, diabetes_y_train)

    # Make predictions using the testing set
    diabetes_y_pred = regressor.predict(diabetes_x_test)

    timer.stop(f"Model MSE: {mean_squared_error(diabetes_y_test, diabetes_y_pred)}")

    return regressor, diabetes_x.columns.tolist()


@pytest.fixture()
def linear_regression_diabetes(linear_regression_diabetes_raw) -> SKLearnModel:
    model, features = linear_regression_diabetes_raw
    return SKLearnModel(
        model,
        model_type=SupportedModelTypes.REGRESSION,
        feature_names=features,
    )


@pytest.fixture(scope="session")
def diabetes_raw_dataset() -> DataFrame:
    loaded = datasets.load_diabetes(as_frame=True)
    raw_data = loaded["data"]
    raw_data["target"] = loaded["target"]
    return raw_data


@pytest.fixture()
def diabetes_dataset(diabetes_raw_dataset: DataFrame) -> Dataset:
    df = diabetes_raw_dataset.drop(columns=["target"])
    column_types = {feature: "numeric" for feature in df.columns.tolist()}
    return Dataset(df, column_types=column_types)


@pytest.fixture()
def diabetes_dataset_with_target(diabetes_raw_dataset: DataFrame) -> Dataset:
    column_types = {feature: "numeric" for feature in diabetes_raw_dataset.columns.tolist()}
    return Dataset(diabetes_raw_dataset, column_types=column_types, target="target")
