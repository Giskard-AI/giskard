import pytest
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error

from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.core.dataset import Dataset
from giskard.core.model import Model
from giskard.ml_worker.utils.logging import Timer
from giskard.models.sklearn import SKLearnModel


@pytest.fixture()
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
def linear_regression_diabetes(linear_regression_diabetes_raw) -> Model:
    diabetes = datasets.load_diabetes()
    return SKLearnModel(
        clf=linear_regression_diabetes_raw,
        model_type=SupportedModelTypes.REGRESSION,
        feature_names=diabetes["feature_names"],
    )


@pytest.fixture()
def diabetes_dataset():
    diabetes = datasets.load_diabetes()
    return Dataset(
        df=datasets.load_diabetes(as_frame=True)["data"],
        feature_types={feature: "numeric" for feature in diabetes["feature_names"]},
        target="target",
    )


@pytest.fixture()
def diabetes_dataset_with_target():
    loaded = datasets.load_diabetes(as_frame=True)
    data = loaded["data"]
    data["target"] = loaded["target"]
    return Dataset(
        df=data,
        feature_types={feature: "numeric" for feature in list(data.columns)},
        column_types=data.dtypes.apply(lambda x: x.name).to_dict(),
        target="target",
    )
