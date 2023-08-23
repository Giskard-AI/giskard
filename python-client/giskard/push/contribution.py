"""
Trigger functions for model debugging contribution notifications.

Functions:

- create_contribution_push: Create contribution push.
- detect_shap_outlier: Detect outlier SHAP value.
- get_shap_values: Get SHAP values for example.
- existing_shap_values: Check if SHAP values exist.

"""
import numpy as np
import pandas as pd
from scipy.stats import zscore

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.models.base.model import BaseModel

from ..models.model_explanation import explain
from ..push import ContributionPush
from .utils import slice_bounds


def create_contribution_push(model: BaseModel, ds: Dataset, df: pd.DataFrame) -> ContributionPush:
    """
    Create contribution notification from SHAP values.

    Analyzes SHAP values to find feature with outlier contribution.
    Checks if contribution results in correct/incorrect prediction.

    If outlier contribution found, creates ContributionPush.

    Args:
        model (BaseModel): ML model
        ds (Dataset): Original dataset
        df (pd.DataFrame): DataFrame with row to analyze

    Returns:
        ContributionPush if outlier contribution found, else None
    """
    if _existing_shap_values(ds):
        shap_res = _detect_shap_outlier(model, ds, df)
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

        if shap_res is not None and ds.column_types[shap_res] != "text":
            bounds = slice_bounds(feature=shap_res, value=values[shap_res].values[0], ds=ds)
            return ContributionPush(
                feature=shap_res,
                value=values[shap_res].values[0],
                bounds=bounds,
                model_type=model.meta.model_type,
                correct_prediction=correct_prediction,
            )


def _detect_shap_outlier(model: BaseModel, ds: Dataset, df: pd.DataFrame):
    """
    Detect outlier SHAP value for a given prediction.

    Computes SHAP values for all features. Calculates z-scores
    to find any significant outliers.

    Args:
        model (BaseModel): ML model
        ds (Dataset): Dataset
        df (pd.DataFrame): DataFrame with row

    Returns:
        Feature name with outlier SHAP value, if any
    """
    feature_shap = _get_shap_values(model, ds, df)
    keys = list(feature_shap.keys())

    zscore_array = np.round(zscore(list(feature_shap.values())) * 2) / 2

    if zscore_array[-1] >= 2:
        return keys[-1]
    else:
        return None


def _get_shap_values(model: BaseModel, ds: Dataset, df: pd.DataFrame):
    """
    Get SHAP values for a model prediction on an example.

    Computes SHAP values that explain the model's output for a given
    input example.

    For classification, returns values for predicted class label.
    For regression, returns values for default output.

    Args:
        model (BaseModel): ML model
        ds (Dataset): Dataset
        df (pd.DataFrame): DataFrame with example row

    Returns:
        Dictionary of SHAP values per feature
    """
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        return explain(model, ds, df.iloc[0])["explanations"][model.meta.classification_labels[0]]
    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        return explain(model, ds, df.iloc[0])["explanations"]["default"]


def _existing_shap_values(ds: Dataset):
    """
    Check if SHAP values can be computed for dataset features.

    SHAP values require at least 2 numerical features.
    Text features are excluded since SHAP is not supported.

    Args:
        ds (Dataset): Dataset

    Returns:
        True if SHAP values can be computed, False otherwise.
    """
    feature_types = list(ds.column_types.values())
    if "text" in feature_types:
        feature_types.remove("text")
    shap_values_exist = len(feature_types) >= 2
    return shap_values_exist
