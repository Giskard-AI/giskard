import numpy as np

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.testing.tests.calibration import (
    _default_overconfidence_threshold,
    test_overconfidence_rate,
    test_underconfidence_rate,
)

from ..push import BorderlinePush, OverconfidencePush


def create_overconfidence_push(model, ds, df):
    row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
    values = row_slice.df
    training_label = values[ds.target].values[0]

    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        model_prediction_results = model.predict(row_slice)

        prediction = model_prediction_results.prediction[0]

        training_label_proba = model_prediction_results.all_predictions[training_label].values[0]
        prediction_proba = model_prediction_results.all_predictions[prediction].values

        if training_label != prediction and (
            prediction_proba - training_label_proba
        ) >= _default_overconfidence_threshold(model):
            rate = test_overconfidence_rate(model, ds).metric
            res = OverconfidencePush(training_label, training_label_proba, row_slice, prediction, rate=rate)
            return res


def create_borderline_push(model, ds, df):
    row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
    prediction_results = model.predict(row_slice)
    values = row_slice.df
    target_value = values[ds.target].values.item()

    if model.is_classification:
        target_value_proba = prediction_results.all_predictions[target_value].values.item()
        if not model.is_binary_classification:
            sorted_predictions = np.sort(prediction_results.raw[0])
            abs_diff = sorted_predictions[-1] - sorted_predictions[-2]
        else:
            threshold = model.meta.classification_threshold
            diff = prediction_results.all_predictions.iloc[0, 1].item() - threshold
            abs_diff = abs(diff)

        if (
            abs_diff <= 0.1
        ):  # TODO: import ai.giskard.config.ApplicationProperties;  applicationProperties.getBorderLineThreshold()
            rate = test_underconfidence_rate(model, ds).metric
            return BorderlinePush(target_value, target_value_proba, row_slice, rate=rate)
