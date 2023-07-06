import numpy as np
from scipy.stats import zscore

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from .utils import slice_bounds
from ..models.model_explanation import explain
from ..push import ContributionPush


def create_contribution_push(model, ds, df):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION and _existing_shap_values(ds):
        shap_res = _contribution_push(model, ds, df)
        slice_df = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
        # slice_df = ds.copy()
        # slice_df.df = df.reset_index(drop=True)
        # slice_df.meta.number_of_rows = 1
        # slice_df = ds.slice(lambda row: row.eq(df.iloc[0]).all(axis=None)) 3 solutions I think the first is the best
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
        shap_res = _contribution_push(model, ds, df)
        slice_df = ds.slice(lambda row: row.equals(df.iloc[0]))
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


def _contribution_push(model, ds, df):
    feature_shap = _get_shap_values(model, ds, df)
    keys = list(feature_shap.keys())

    zscore_array = np.round(zscore(list(feature_shap.values())) * 2) / 2

    k1 = keys[-1]
    if zscore_array[-1] >= 2:
        return [k1]
    else:
        return None


def _get_shap_values(model, ds, df):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        return explain(model, ds, df.iloc[0])["explanations"][model.meta.classification_labels[0]]
    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        return explain(model, ds, df.iloc[0])["explanations"]["default"]


def _existing_shap_values(ds):
    feature_types = list(ds.column_types.values())
    if "text" in feature_types:
        feature_types.remove("text")
    shap_values_exist = len(feature_types) >= 2
    return shap_values_exist
