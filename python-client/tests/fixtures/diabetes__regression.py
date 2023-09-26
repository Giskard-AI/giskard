import pytest
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error

from giskard.datasets.base import Dataset
from giskard.models.sklearn import SKLearnModel
from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.utils.logging import Timer


@pytest.fixture(scope="session")
def linear_regression_diabetes_raw():
    timer = Timer()
    diabetes = datasets.load_diabetes()

    diabetes_x = diabetes["data"]
    diabetes_y = diabetes["target"]

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

    return regressor


@pytest.fixture()
def linear_regression_diabetes(linear_regression_diabetes_raw) -> SKLearnModel:
    diabetes = datasets.load_diabetes()
    return SKLearnModel(
        linear_regression_diabetes_raw,
        model_type=SupportedModelTypes.REGRESSION,
        feature_names=diabetes["feature_names"],
    )


@pytest.fixture()
def diabetes_dataset() -> Dataset:
    diabetes = datasets.load_diabetes()
    raw_data = datasets.load_diabetes(as_frame=True)["data"]
    column_types = {feature: "numeric" for feature in diabetes["feature_names"]}

    wrapped_data = Dataset(raw_data, column_types=column_types)
    return wrapped_data


@pytest.fixture()
def diabetes_dataset_with_target() -> Dataset:
    loaded = datasets.load_diabetes(as_frame=True)

    raw_data = loaded["data"]
    raw_data["target"] = loaded["target"]
    column_types = {feature: "numeric" for feature in list(raw_data.columns)}

    wrapped_data = Dataset(raw_data, target="target", column_types=column_types)
    return wrapped_data
