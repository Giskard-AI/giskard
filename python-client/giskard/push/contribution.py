import numpy as np
import pandas as pd
from scipy.stats import zscore

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.models.base.model import BaseModel

from ..models.model_explanation import explain
from ..push import ContributionPush
from .utils import slice_bounds


def create_contribution_push(model, ds, df):
    if existing_shap_values(ds):
        shap_res = detect_shap_outlier(model, ds, df)
        slice_df = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
        values = slice_df.df

        if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
            training_label = values[ds.target].values[0]
            prediction = model.predict(slice_df).prediction[0]

            correct_prediction = training_label == prediction

        if model.meta.model_type == SupportedModelTypes.REGRESSION:
            y = values[ds.target].values[0]
            y_hat = model.predict(slice_df).prediction[0]
            error = abs(y_hat - y)

            correct_prediction = abs(error - y) / y < 0.2

        if shap_res is not None:
            bounds = slice_bounds(feature=shap_res, value=values[shap_res].values[0], ds=ds)
            return ContributionPush(
                feature=shap_res,
                value=values[shap_res].values[0],
                bounds=bounds,
                model_type=SupportedModelTypes.REGRESSION,
                correct_prediction=correct_prediction,
            )


def detect_shap_outlier(model: BaseModel, ds: Dataset, df: pd.DataFrame):
    feature_shap = get_shap_values(model, ds, df)
    keys = list(feature_shap.keys())

    zscore_array = np.round(zscore(list(feature_shap.values())) * 2) / 2

    if zscore_array[-1] >= 2:
        return keys[-1]
    else:
        return None


def get_shap_values(model: BaseModel, ds: Dataset, df: pd.DataFrame):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        return explain(model, ds, df.iloc[0])["explanations"][model.meta.classification_labels[0]]
    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        return explain(model, ds, df.iloc[0])["explanations"]["default"]


def existing_shap_values(ds: Dataset):
    feature_types = list(ds.column_types.values())
    if "text" in feature_types:
        feature_types.remove("text")
    shap_values_exist = len(feature_types) >= 2
    return shap_values_exist
