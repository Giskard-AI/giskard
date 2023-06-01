import numpy as np
import pandas as pd

import tests.utils
from giskard import Dataset
from giskard.models.automodel import Model


def test_autoserializablemodel_arbitrary():
    class MyArbitraryModel(Model):
        def model_predict(self, df):
            return np.array(df["x"]).astype(float)

    my_model = MyArbitraryModel(
        model=lambda x: x ** 2,
        model_type="regression",
    )

    my_dataset = Dataset(df=pd.DataFrame({"x": [1, 2], "y": [1, 2]}), target="y")

    tests.utils.verify_model_upload(my_model, my_dataset)


def test_autoserializablemodel_sklearn(german_credit_raw_model, german_credit_data):
    class my_custom_model(Model):
        def model_predict(self, some_df: pd.DataFrame):
            return self.model.predict_proba(some_df)

    my_model = my_custom_model(
        model=german_credit_raw_model,
        model_type="classification",
        classification_labels=german_credit_raw_model.classes_,
        classification_threshold=0.5,
    )

    tests.utils.verify_model_upload(my_model, german_credit_data)
