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
from .utils import slice_bounds_relative


def _get_model_predictions(model: BaseModel, sliced_ds: Dataset):
    """
    Get raw prediction and determine if the prediction is correct for a given model.

    Args:
        model (BaseModel): The model.
        sliced_ds (Dataset): The sliced dataset.

    Returns:
        Tuple: A tuple containing raw_prediction and correct_prediction.
            - raw_prediction: The raw prediction from the model.
            - correct_prediction: True if the prediction is correct, False otherwise.
    """
    raw_prediction, correct_prediction = None, None

    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        training_label = sliced_ds.df[sliced_ds.target].values[0]
        predictions = model.predict(sliced_ds)
        prediction = predictions.prediction[0]

        raw_prediction = predictions.raw_prediction[0]
        correct_prediction = training_label == prediction

    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        y_hat = model.predict(sliced_ds).prediction[0]
        y = sliced_ds.df[sliced_ds.target].values[0]
        error = abs(y_hat - y)

        correct_prediction = abs(error - y) / y < 0.2

    return raw_prediction, correct_prediction


def _create_non_text_contribution_push(shap_feature, sliced_ds, ds, model, correct_prediction):
    """
    Create a ContributionPush object for non-text features with outlier contributions.

    Args:
        shap_feature (str): The most important feature detected by SHAP.
        sliced_ds (Dataset): The sliced dataset.
        ds (Dataset): The original dataset.
        model (BaseModel): The model.
        correct_prediction (bool): True if the prediction is correct, False otherwise.

    Returns:
        ContributionPush: An object representing the contribution push for non-text features.
    """
    # Calculate bounds for the feature
    bounds = slice_bounds_relative(feature=shap_feature, value=sliced_ds.df[shap_feature].values[0], ds=ds)

    # Create the ContributionPush object
    return ContributionPush(
        feature=shap_feature,
        value=sliced_ds.df[shap_feature].values[0],
        bounds=bounds,
        model_type=model.meta.model_type,
        correct_prediction=correct_prediction,
    )


def _create_text_contribution_push(shap_feature, sliced_ds, model, raw_prediction, correct_prediction):
    """
    Create a ContributionPush object for text features.

    Args:
        shap_feature (str): The most important text feature detected by SHAP.
        sliced_ds (Dataset): The sliced dataset.
        model (BaseModel): The model.
        raw_prediction (float): The raw prediction score from the model.
        correct_prediction (bool): True if the prediction is correct, False otherwise.

    Returns:
        ContributionPush: An object representing the contribution push for text features.
    """
    # Explain the text feature
    input_df = model.prepare_dataframe(sliced_ds.df, column_dtypes=sliced_ds.column_dtypes, target=sliced_ds.target)

    text_explanation = explain_text(
        model=model,
        input_df=input_df,
        text_column=shap_feature,
        text_document=sliced_ds.df[shap_feature].iloc[0],
    )

    # Create a dictionary mapping words to their importance scores
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        text_explanation_map = dict(zip(text_explanation[0], text_explanation[1][raw_prediction]))
    else:
        text_explanation_map = dict(zip(text_explanation[0], text_explanation[1]))

    # Detect the most important word based on the explanation
    most_important_word = _detect_text_shap_outlier(text_explanation_map)

    # If for any reason, the most_important_word is not found, don't create a push notification
    if most_important_word is not None:
        return ContributionPush(
            feature=shap_feature,
            feature_type="text",
            value=most_important_word,
            model_type=model.meta.model_type,
            correct_prediction=correct_prediction,
        )


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
    # Check if there is only one feature type in the dataset, and if it's "text"
    _text_is_the_only_feature = len(ds.column_types.values()) == 1 and list(ds.column_types.values())[0] == "text"

    # Get global SHAP values for the model's predictions on the input DataFrame
    global_feature_shap = _get_shap_values(model, ds, df)

    # Detect the SHAP feature with outlier contribution, if SHAP values exist
    shap_feature = _detect_shap_outlier(global_feature_shap) if _existing_shap_values(ds) else None

    # Check if a SHAP feature with outlier contribution was detected
    _shap_outlier_detected = shap_feature is not None

    # Determine if model predictions are needed based on the presence of outlier SHAP features and target variable
    _model_predictions_needed = (_shap_outlier_detected or _text_is_the_only_feature) and ds.target is not None

    # If model predictions are needed, continue
    if _model_predictions_needed:
        # Choose the SHAP feature for analysis, considering the case when there's only one text feature
        shap_feature = shap_feature if not _text_is_the_only_feature else list(ds.column_types.keys())[0]

        # Check if the SHAP feature is not a text feature
        _shap_feature_is_not_text = _shap_outlier_detected and ds.column_types[shap_feature] != "text"

        # Check if the SHAP feature is a text feature or it's the only feature in the dataset
        _shap_feature_is_text = _shap_outlier_detected and ds.column_types[shap_feature] == "text"

        # Create a new dataset for analysis, copying the column types and excluding validation
        sliced_ds = Dataset(
            df=df,
            target=ds.target,
            column_types=ds.column_types.copy(),
            validation=False,
        )

        # Get raw and correct predictions from the model for the sliced dataset
        raw_prediction, correct_prediction = _get_model_predictions(model, sliced_ds)

        # If the SHAP feature is not a text feature, create a non-text ContributionPush
        if _shap_feature_is_not_text:
            return _create_non_text_contribution_push(shap_feature, sliced_ds, ds, model, correct_prediction)

        # If the SHAP feature is a text feature or it's the only feature, create a text ContributionPush
        elif _shap_feature_is_text or _text_is_the_only_feature:
            return _create_text_contribution_push(shap_feature, sliced_ds, model, raw_prediction, correct_prediction)


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
