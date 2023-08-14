import pandas as pd

from giskard.datasets.base import Dataset
from giskard.models.base.model import BaseModel
from giskard.testing.tests.calibration import (
    test_overconfidence_rate,
    test_underconfidence_rate,
)

from ..push import BorderlinePush, OverconfidencePush


def create_overconfidence_push(model: BaseModel, ds: Dataset, df: pd.DataFrame):
    if model.is_classification:
        row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)

        values = row_slice.df
        training_label = values[ds.target].values[0]
        model_prediction_results = model.predict(row_slice)
        training_label_proba = model_prediction_results.all_predictions[training_label].values[0]
        prediction = model_prediction_results.prediction[0]

        test_result = test_overconfidence_rate(model, row_slice).execute()
        if not test_result.passed and training_label != prediction:
            return OverconfidencePush(
                training_label, training_label_proba, row_slice, prediction, rate=test_result.metric
            )


def create_borderline_push(model: BaseModel, ds: Dataset, df: pd.DataFrame):
    if model.is_classification:
        row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
        values = row_slice.df
        target_value = values[ds.target].values.item()
        prediction_results = model.predict(row_slice)
        target_value_proba = prediction_results.all_predictions[target_value].values.item()
        test_result = test_underconfidence_rate(model, row_slice).execute()
        if not test_result.passed:
            return BorderlinePush(target_value, target_value_proba, row_slice, rate=test_result.metric)
