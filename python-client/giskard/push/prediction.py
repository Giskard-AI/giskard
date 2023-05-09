from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.testing.tests.performance import test_rmse


def overconfidence(model, ds, idrow):
    values = ds.df.iloc[idrow]
    training_label = values[ds.target]
    row_slice = ds.slice(lambda x: x.loc[[idrow]], row_level=False)
    model_prediction_results = model.predict(row_slice)

    prediction = model_prediction_results.prediction

    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        probabilities = model_prediction_results.probabilities
        if training_label != prediction and probabilities[0] > 0.75:  # use scan feature ?
            # res = Push(push_type="contribution_wrong", feature=el,
            #            value=values[el],
            #            bounds=bounds
            #            )
            return probabilities

    if model.meta.model_type == SupportedModelTypes.REGRESSION: # @TODO: SKlearn model no target
        y_hat = prediction
        y = values[ds.target]
        error = abs(y_hat - y)
        rmse_res = test_rmse(ds, model).execute()
        if abs(error - rmse_res.metric) / rmse_res.metric >= 0.75:
            return error, rmse_res.metric


def borderline(model, ds, idrow):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        row_slice = ds.slice(lambda x: x.loc[[idrow]], row_level=False)
        model_prediction_results = model.predict(row_slice)
        probabilities = model_prediction_results.probabilities
        if probabilities[0] < 0.55:  # use scan feature ?
            # res = Push(push_type="contribution_wrong", feature=el,
            #            value=values[el],
            #            bounds=bounds
            #            )
            return probabilities


def stochasticity(model, ds, idrow):
    res_first = model.predict(ds.slice(lambda x: x.loc[[idrow]], row_level=False))
    res_second = model.predict(ds.slice(lambda x: x.loc[[idrow]], row_level=False))
    if res_first.prediction != res_second.prediction:
        return "stochasticity"

# def data_leakage(model, ds, idrow): @TODO: Still needed to be done
#     if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
#         row_slice = ds.slice(lambda x: x.loc[[idrow]], row_level=False)
#         model_prediction_results = model.predict(row_slice)
