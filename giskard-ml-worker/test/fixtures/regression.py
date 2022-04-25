import logging

import pytest
from ai_inspector import ModelInspector
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error

from test.test_utils import timing


@pytest.fixture()
def diabetes_dataset():
    return datasets.load_diabetes(as_frame=True)['data']


@pytest.fixture()
def diabetes_dataset_with_target():
    loaded = datasets.load_diabetes(as_frame=True)
    data = loaded['data']
    data['target'] = loaded['target']
    return data


@pytest.fixture()
@timing
def linear_regression_diabetes() -> ModelInspector:
    diabetes = datasets.load_diabetes()

    diabetes_x = diabetes['data']
    diabetes_y = diabetes['target']

    # Split the data into training/testing sets
    diabetes_x_train = diabetes_x[:-20]
    diabetes_x_test = diabetes_x[-20:]

    # Split the targets into training/testing sets
    diabetes_y_train = diabetes_y[:-20]
    diabetes_y_test = diabetes_y[-20:]

    # Create linear regression object
    regr = linear_model.LinearRegression()

    # Train the model using the training sets
    regr.fit(diabetes_x_train, diabetes_y_train)

    # Make predictions using the testing set
    diabetes_y_pred = regr.predict(diabetes_x_test)

    logging.info(f"Model MSE: {mean_squared_error(diabetes_y_test, diabetes_y_pred)}")

    return ModelInspector(
        prediction_function=regr.predict,
        prediction_task='regression',
        input_types={feature: 'numeric' for feature in diabetes['feature_names']},
    )
