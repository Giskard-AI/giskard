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
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        # row_slice = ds.slice(lambda x: x.loc[[idrow]], row_level=False)
        row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
        model_prediction_results = model.predict(row_slice)
        all_predictions = model_prediction_results.all_predictions
        diff, max, second = _var(all_predictions)
        values = row_slice.df
        training_label = values[ds.target].values[0]
        training_label_proba = model_prediction_results.all_predictions[training_label].values[0]

        if diff <= 0.1:
            return BorderlinePush(max, second, training_label, training_label_proba, row_slice)


def _var(x):
    row_as_list = x.values.flatten().tolist()
    max_val = max(row_as_list)
    row_as_list.remove(max_val)
    second_max_val = max(row_as_list)
    diff = max_val - second_max_val
    # diff = abs(max_val - second_max_val)/second_max_val
    # diff = abs(max_val - second_max_val)
    return diff, max_val, second_max_val
