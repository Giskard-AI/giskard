import pandas as pd
import tests.utils

from giskard import Model


def test_autoserializablemodel(german_credit_raw_model, german_credit_data):
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
