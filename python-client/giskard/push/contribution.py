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

from ..models.model_explanation import explain, explain_text
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
    _text_is_the_only_feature = len(ds.column_types.values()) == 1 and list(ds.column_types.values())[0] == "text"
    global_feature_shap = _get_shap_values(model, ds, df)
    shap_res = _detect_shap_outlier(global_feature_shap) if _existing_shap_values(ds) else None
    _shap_outlier_detected = shap_res is not None
    shap_res = shap_res if not _text_is_the_only_feature else list(ds.column_types.keys())[0]
    _most_important_feature_is_not_text = _shap_outlier_detected and ds.column_types[shap_res] != "text"
    _most_important_feature_is_text = _shap_outlier_detected and ds.column_types[shap_res] == "text"
    _compute_predictions = _shap_outlier_detected or _text_is_the_only_feature

    if _compute_predictions:
        slice_df = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)
        values = slice_df.df

        if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
            training_label = values[ds.target].values[0] if ds.target is not None else None
            predictions = model.predict(slice_df)
            prediction = predictions.prediction[0]
            raw_prediction = predictions.raw_prediction[0]

            correct_prediction = training_label == prediction if training_label is not None else None
        elif model.meta.model_type == SupportedModelTypes.REGRESSION:
            y = values[ds.target].values[0]
            y_hat = model.predict(slice_df).prediction[0]
            error = abs(y_hat - y)

            correct_prediction = abs(error - y) / y < 0.2

        if _most_important_feature_is_not_text:
            bounds = slice_bounds(feature=shap_res, value=values[shap_res].values[0], ds=ds)
            return ContributionPush(
                feature=shap_res,
                value=values[shap_res].values[0],
                bounds=bounds,
                model_type=model.meta.model_type,
                correct_prediction=correct_prediction,
            )
        elif _most_important_feature_is_text or _text_is_the_only_feature:
            text_explanation = explain_text(
                model=model, input_df=df, text_column=shap_res, text_document=df[shap_res].iloc[0]
            )
            if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
                text_explanation_map = dict(zip(text_explanation[0], text_explanation[1][raw_prediction]))
            else:
                text_explanation_map = dict(zip(text_explanation[0], text_explanation[1]))

            most_important_word = _detect_text_shap_outlier(text_explanation_map)

            return ContributionPush(
                feature=shap_res,
                feature_type="text",
                value=most_important_word,
                model_type=model.meta.model_type,
                correct_prediction=correct_prediction,
            )


def _detect_shap_outlier(global_feature_shap):
    """
    Detect outlier SHAP value for a given prediction.

    Computes SHAP values for all features. Calculates z-scores
    to find any significant outliers.

    Args:
        global_feature_shap (np.ndarray): Output of the explain() function: a summary of the shap explanation

    Returns:
        Feature name with outlier SHAP value, if any
    """
    keys = list(global_feature_shap.keys())

    zscore_array = np.round(zscore(list(global_feature_shap.values())) * 2) / 2

    if zscore_array[-1] >= 2:
        return keys[-1]
    else:
        return None


def _detect_text_shap_outlier(global_feature_shap):
    """
    Detect outlier SHAP value for a given prediction.

    Computes SHAP values for all features. Calculates z-scores
    to find any significant outliers.

    Args:
        global_feature_shap (np.ndarray): Output of the explain_text() function: a summary of the shap explanation

    Returns:
        Feature name with outlier SHAP value, if any
    """
    keys = list(global_feature_shap.keys())

    zscore_array = zscore(list(global_feature_shap.values()))
    max_idx = np.argmax(zscore_array)

    if zscore_array[max_idx] >= 2:
        return keys[max_idx]
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
