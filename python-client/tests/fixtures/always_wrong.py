import pandas as pd
import pytest
from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel, logger
import numpy as np
from sklearn.dummy import DummyClassifier
from tests import path

input_types = {
    "input": "numeric",
    "sex": "category"
}


@pytest.fixture()
def always_wrong_data() -> GiskardDataset:
    logger.info("Reading always_wrong.csv")
    df = pd.read_csv(path("test_data/always_wrong.csv"), keep_default_na=False, na_values=["_GSK_NA_"])
    return GiskardDataset(
        df=df,
        column_types=df.dtypes.apply(lambda x: x.name).to_dict(),
        target="output",
        feature_types=input_types
    )


@pytest.fixture()
def always_wrong_model() -> GiskardModel:
    X = np.array([0])
    y = np.array(["0"])

    dummy = DummyClassifier(strategy="constant", constant=np.array(["0"]))
    dummy.fit(X, y)

    # I'm using a DummyClassifier to output a string, but specifying a Regression model for simplicity...
    # I do not like this it's very hacky.
    return GiskardModel(
        prediction_function=dummy.predict,
        model_type='regression',
        feature_names=list(input_types)
    )
