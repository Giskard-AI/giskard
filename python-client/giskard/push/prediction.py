import numpy as np
import pandas as pd
from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset

from ..push import BorderlinePush, OverconfidencePush

from giskard.testing.tests.calibration import _default_overconfidence_threshold


def create_overconfidence_push(model, ds, df):
    # row_slice = ds.slice(lambda df: df.loc[[idrow]], row_level=False)
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
            # if training_label != prediction and prediction_proba >= 2* training_label_proba:
            # res = Push(push_type="contribution_wrong", feature=el,
            #            value=values[el],
            #            bounds=bounds
            #            )
            res = OverconfidencePush(training_label, training_label_proba, row_slice, prediction)
            return res


def create_borderline_push(model, ds, df):
    row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
    prediction_results = model.predict(row_slice)
    values = row_slice.df
    training_label = values[ds.target].values[0]
    training_label_proba = prediction_results.all_predictions[training_label].values[0]

    if model.is_classification:
        results = prediction_results.all_predictions
        labels = {k: v for k, v in enumerate(model.meta.classification_labels)}

        if len(model.meta.classification_labels) > 2 or model.meta.classification_threshold is None:
            preds_serie = prediction_results.all_predictions.idxmax(axis="columns")
            sorted_predictions = np.sort(prediction_results.all_predictions.values)
            abs_diff = pd.Series(
                sorted_predictions[:, -1] - sorted_predictions[:, -2],
                name="absDiff",
            )
        else:
            diff = prediction_results.all_predictions.iloc[:, 1] - model.meta.classification_threshold
            preds_serie = (diff >= 0).astype(int).map(labels).rename("predictions")
            abs_diff = pd.Series(diff.abs(), name="absDiff")

    else:
        results = pd.Series(prediction_results.prediction)
        preds_serie = results
        if row_slice.target and row_slice.target in row_slice.df.columns:
            target_serie = row_slice.df[row_slice.target]

            diff = preds_serie - target_serie

            abs_diff = pd.Series(
                diff.abs(),
                name="absDiff",
                dtype=np.float64,
            )

    if (
        abs_diff <= 0.1
    ):  # TODO: import ai.giskard.config.ApplicationProperties;  applicationProperties.getBorderLineThreshold()
        return BorderlinePush(training_label, training_label_proba, row_slice)
