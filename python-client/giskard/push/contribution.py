import numpy as np
from scipy.stats import zscore

from giskard.core.core import SupportedModelTypes
from .utils import slice_bounds
from ..models.model_explanation import explain
from ..push import ContributionPush


def create_contribution_push(model, ds, idrow):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION and _existing_shap_values(ds):
        shap_res = _contribution_push(model, ds, idrow)
        slice_df = ds.slice(lambda df: df.loc[[idrow]], row_level=False)
        values = slice_df.df
        training_label = values[ds.target].values[0]
        prediction = model.predict(slice_df).prediction[0]
        if shap_res is not None:
            for el in shap_res:
                bounds = slice_bounds(feature=el, value=values[el].values[0], ds=ds)

                if training_label != prediction:
                    res = ContributionPush(
                        feature=el,
                        value=values[el].values[0],
                        bounds=bounds,
                        model_type=SupportedModelTypes.CLASSIFICATION,
                        correct_prediction=False,
                    )
                    return res

                else:
                    res = ContributionPush(
                        feature=el,
                        value=values[el].values[0],
                        bounds=bounds,
                        model_type=SupportedModelTypes.CLASSIFICATION,
                        correct_prediction=True,
                    )
                    return res

    if model.meta.model_type == SupportedModelTypes.REGRESSION and _existing_shap_values(ds):
        shap_res = _contribution_push(model, ds, idrow)
        slice_df = ds.slice(lambda df: df.loc[[idrow]], row_level=False)
        values = slice_df.df

        y = values[ds.target].values[0]
        y_hat = model.predict(slice_df).prediction[0]
        error = abs(y_hat - y)

        if shap_res is not None:
            for el in shap_res:
                bounds = slice_bounds(feature=el, value=values[el].values[0], ds=ds)
                if abs(error - y) / y >= 0.2:
                    res = ContributionPush(
                        feature=el,
                        value=values[el].values[0],
                        bounds=bounds,
                        model_type=SupportedModelTypes.REGRESSION,
                        correct_prediction=False,
                    )
                    return res

                else:
                    res = ContributionPush(
                        feature=el,
                        value=values[el].values[0],
                        bounds=bounds,
                        model_type=SupportedModelTypes.REGRESSION,
                        correct_prediction=True,
                    )
                    return res


def _contribution_push(model, ds, idrow):
    feature_shap = _get_shap_values(model, ds, idrow)
    keys = list(feature_shap.keys())

    zscore_array = np.round(zscore(list(feature_shap.values())) * 2) / 2

    k1, k2 = keys[-1], keys[-2]
    if zscore_array[-1] >= 2:
        return [k1]
    elif zscore_array[-1] >= 1.5 and zscore_array[-2] >= 1:
        return [k1, k2]
    else:
        return None


def _get_shap_values(model, ds, idrow):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        return explain(model, ds, ds.df.iloc[idrow])["explanations"][model.meta.classification_labels[0]]
    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        return explain(model, ds, ds.df.iloc[idrow])["explanations"]["default"]


def _existing_shap_values(ds):
    feature_types = list(ds.column_types.values())
    if "text" in feature_types:
        feature_types.remove("text")
    shap_values_exist = len(feature_types) >= 2
    return shap_values_exist
