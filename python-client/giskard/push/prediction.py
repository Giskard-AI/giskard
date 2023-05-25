from giskard.core.core import SupportedModelTypes
from ..push import OverconfidencePush, BorderlinePush


def overconfidence(model, ds, idrow):
    values = ds.df.loc[[idrow]]
    training_label = values[ds.target].values

    row_slice = ds.slice(lambda df: df.loc[[idrow]], row_level=False)
    model_prediction_results = model.predict(row_slice)

    prediction = model_prediction_results.prediction

    training_label_proba = model_prediction_results.all_predictions[training_label].values
    prediction_proba = model_prediction_results.all_predictions[prediction].values

    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        if training_label != prediction and prediction_proba >= 1.5 * training_label_proba:
            # if training_label != prediction and prediction_proba >= 2* training_label_proba:
            # res = Push(push_type="contribution_wrong", feature=el,
            #            value=values[el],
            #            bounds=bounds
            #            )
            res = OverconfidencePush(training_label, training_label_proba, row_slice,prediction)
            return res


def borderline(model, ds, idrow):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:

        row_slice = ds.slice(lambda x: x.loc[[idrow]], row_level=False)
        model_prediction_results = model.predict(row_slice)
        all_predictions = model_prediction_results.all_predictions
        diff, max, second = _var_rate(all_predictions)

        values = ds.df.loc[[idrow]]
        training_label = values[ds.target].values
        training_label_proba = model_prediction_results.all_predictions[training_label].values

        if diff <= 0.2:
            return BorderlinePush(max, second, training_label, training_label_proba, row_slice)


def _var_rate(x):
    row_as_list = x.values.flatten().tolist()
    max_val = max(row_as_list)
    row_as_list.remove(max_val)
    second_max_val = max(row_as_list)
    diff = 2 * abs(max_val - second_max_val) / (max_val + second_max_val)
    # diff = abs(max_val - second_max_val)/second_max_val
    # diff = abs(max_val - second_max_val)
    return diff, max_val, second_max_val
