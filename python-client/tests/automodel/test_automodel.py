import numpy as np
import pandas as pd
import pytest
import tests.utils
from giskard import Dataset
from giskard.models.automodel import Model
from giskard.models.function import PredictionFunctionModel
from giskard.models.sklearn import SKLearnModel


class MyArbitraryModel(Model):
    def model_predict(self, df):
        return np.array(df["x"]).astype(float)


class MySklearnModel(Model):
    def model_predict(self, some_df: pd.DataFrame):
        return self.model.predict_proba(some_df)


def test_autoserializablemodel_abstract():
    class UnsupportedModel:
        ...

    unsupported_model = UnsupportedModel()
    with pytest.raises(NotImplementedError) as e:
        Model(model=unsupported_model, model_type="regression")
    assert e.match(
        "We could not infer your model library.*")


def test_autoserializablemodel_arbitrary_default():
    def prediction_function(df):
        return df['x'] ** 2

    my_model = Model(model=prediction_function, model_type="regression")

    my_dataset = Dataset(df=pd.DataFrame({"x": [1., 2.], "y": [1, 2]}), target="y")

    assert isinstance(my_model, PredictionFunctionModel)
    tests.utils.verify_model_upload(my_model, my_dataset)


def test_autoserializablemodel_sklearn_default(german_credit_raw_model, german_credit_data):
    my_model = Model(
        model=german_credit_raw_model,
        model_type="classification",
        classification_labels=german_credit_raw_model.classes_,
        classification_threshold=0.5,
    )

    assert isinstance(my_model, SKLearnModel)
    tests.utils.verify_model_upload(my_model, german_credit_data)


def test_autoserializablemodel_arbitrary():
    my_model = MyArbitraryModel(
        model=lambda x: x ** 2,
        model_type="regression",
    )

    my_dataset = Dataset(df=pd.DataFrame({"x": [1, 2], "y": [1, 2]}), target="y")

    assert isinstance(my_model, PredictionFunctionModel)
    tests.utils.verify_model_upload(my_model, my_dataset)


def test_autoserializablemodel_sklearn(german_credit_raw_model, german_credit_data):
    my_model = MySklearnModel(
        model=german_credit_raw_model,
        model_type="classification",
        classification_labels=german_credit_raw_model.classes_,
        classification_threshold=0.5,
    )

    assert isinstance(my_model, SKLearnModel)
    tests.utils.verify_model_upload(my_model, german_credit_data)
