from typing import Any, Callable, Dict, List

import logging
import warnings

import numpy as np
import pandas as pd

from giskard.core.errors import GiskardImportError
from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel
from giskard.utils.logging_utils import timer

warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")
logger = logging.getLogger(__name__)


def _get_background_example(df: pd.DataFrame, feature_types: Dict[str, str]) -> pd.DataFrame:
    """Create a background example for the SHAP Kernel explainer.

    For numerical features a median is used. For categorical features a mode
    is used.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset used to calculate background feature values.

    feature_types : dict of str
        Mapping between the feature names and their types (numeric, category or text)

    Returns
    -------
    background_sample : pd.DataFrame
        Calculated background sample.
    """
    median = df.median(numeric_only=True)
    background_sample = df.mode(dropna=False).head(1)

    # Use median of the numerical features.
    numerical_features = [feature for feature in list(df.columns) if feature_types.get(feature) == "numeric"]
    for feature in numerical_features:
        background_sample[feature] = median[feature]

    background_sample = background_sample.astype(df.dtypes)
    return background_sample


def _get_columns_original_order(prepared_dataset: Dataset, model: BaseModel, dataset: Dataset) -> list:
    """Return the columns of the `prepared_dataset` in the original order.

    Use `model` or `dataset` to deduce the original sequence of columns that
    the model was initially trained with.

    Parameters
    ----------
    prepared_dataset : giskard.Dataset
        The dataset used for the SHAP explanation.

    model : giskard.Model
        The model that potentially contains columns order information.

    dataset: giskard.Dataset
        The reference dataset that potentially contains columns order
        information.

    Returns
    -------
    list
        A list of column names in the order that the model was trained with.
    """
    features_names = model.feature_names
    return features_names if features_names else [c for c in dataset.df.columns if c in prepared_dataset.df.columns]


def _prepare_for_explanation(input_df: pd.DataFrame, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
    """Prepare dataframe for a SHAP explanation.

    Check the dataframe columns and their order, and cast columns to their
    data types.

    Parameters
    ----------
    input_df : pd.DataFrame
        The dataset used for the SHAP explanation.

    model: giskard.Model
        The model used for the SHAP explanation.

    dataset: giskard.Dataset
        Reference dataset, which contains metadata used to prepare `input_df`.

    Returns
    -------
    prepared_df : pd.DataFrame
        Dataset prepared for the SHAP explanation.
    """
    input_df = model.prepare_dataframe(input_df, column_dtypes=dataset.column_dtypes, target=dataset.target)

    target = dataset.target if dataset.target in input_df.columns else None
    prepared_dataset = Dataset(input_df, column_types=dataset.column_types, target=target, validation=False)
    prepared_df = prepared_dataset.df[_get_columns_original_order(prepared_dataset, model, dataset)]
    return prepared_df


def _calculate_dataset_shap_values(model: BaseModel, dataset: Dataset) -> np.ndarray:
    """Perform Kernel SHAP explanation of the `dataset` entries.

    Returns the feature importance in terms of SHAP values. Kernel SHAP is used
    to calculate feature contributions.

    Parameters
    ----------
    model : giskard.Model
        The model used for the SHAP explanation.

    dataset : giskard.Dataset
        The dataset used for the SHAP explanation.

    Returns
    -------
    shap_values : np.ndarray
        The model's SHAP values as a numpy array
    """
    try:
        from shap import KernelExplainer
    except ImportError as e:
        raise GiskardImportError("shap") from e

    # Prepare background sample to be used in the KernelSHAP.
    background_df = model.prepare_dataframe(dataset.df, dataset.column_dtypes, dataset.target)
    background_sample = _get_background_example(background_df, dataset.column_types)

    # Prepare input data for an explanation.
    data_to_explain = _prepare_for_explanation(dataset.df, model=model, dataset=dataset)

    def prediction_function(_df):
        """Rolls-back SHAP casting of all columns to the 'object' type."""
        return model.predict_df(_df.astype(data_to_explain.dtypes))

    # Obtain SHAP explanations.
    explainer = KernelExplainer(prediction_function, background_sample, data_to_explain.columns, keep_index=True)
    shap_values = explainer.shap_values(data_to_explain, silent=True)
    return shap_values


def _get_highest_proba_shap(shap_values: np.ndarray, model: BaseModel, dataset: Dataset) -> list:
    """Get the SHAP values of the prediction with the highest probability.

    Parameters
    ----------
    shap_values : np.ndarray (n_classes x n_samples)
        The model's SHAP values as a numpy array

    model : giskard.Model
        The model used for the SHAP explanation

    dataset : giskard.Dataset
        The dataset used for the SHAP explanation.

    Returns
    -------
    list
        SHAP values of the prediction with the highest probability
    """
    predictions = model.predict(dataset).raw_prediction
    return [shap_values[predicted_class][sample_idx] for sample_idx, predicted_class in enumerate(predictions)]


def explain_with_shap(model: BaseModel, dataset: Dataset, only_highest_proba: bool = True):
    """Explain the model with SHAP and return the results as a `ShapResult` object.

    Parameters
    ----------
    model : giskard.Model
        The model used for the SHAP explanation

    dataset : giskard.Dataset
        The dataset used for the SHAP explanation.

    only_highest_proba : bool (optional, default=True)
        A flag indicating whether to provide SHAP explanations only for the
        predictions with the highest probability or not.

    Returns
    -------
    ShapResult
        The model's SHAP values.
    """

    try:
        from shap import Explanation

        from giskard.models.shap_result import ShapResult
    except ImportError as e:
        raise GiskardImportError("shap") from e
    shap_values = _calculate_dataset_shap_values(model, dataset)
    if only_highest_proba and model.is_classification:
        shap_values = _get_highest_proba_shap(shap_values, model, dataset)

    # Put SHAP values to the Explanation object for a convenience.
    feature_names = model.feature_names or list(dataset.df.columns.drop(dataset.target, errors="ignore"))
    shap_explanations = Explanation(shap_values, data=dataset.df[feature_names], feature_names=feature_names)

    feature_types = {key: dataset.column_types[key] for key in feature_names}
    return ShapResult(shap_explanations, feature_types, model.model_type, only_highest_proba)


def _calculate_sample_shap_values(model: BaseModel, dataset: Dataset, input_data: Dict) -> np.ndarray:
    try:
        from shap import KernelExplainer
    except ImportError as e:
        raise GiskardImportError("shap") from e

    df = model.prepare_dataframe(dataset.df, column_dtypes=dataset.column_dtypes, target=dataset.target)
    data_to_explain = _prepare_for_explanation(pd.DataFrame([input_data]), model=model, dataset=dataset)

    def predict_array(array):
        arr_df = pd.DataFrame(array, columns=list(df.columns))
        return model.predict_df(_prepare_for_explanation(arr_df, model=model, dataset=dataset))

    example = _get_background_example(df, dataset.column_types)
    kernel = KernelExplainer(predict_array, example)
    shap_values = kernel.shap_values(data_to_explain, silent=True)
    return shap_values


@timer()
def explain(model: BaseModel, dataset: Dataset, input_data: Dict):
    shap_values = _calculate_sample_shap_values(model, dataset, input_data)
    feature_names = model.feature_names or list(dataset.df.columns.drop(dataset.target, errors="ignore"))

    if model.is_regression:
        explanation_chart_data = summary_shap_regression(shap_values=shap_values, feature_names=feature_names)
    elif model.is_classification:
        explanation_chart_data = summary_shap_classification(
            shap_values=shap_values,
            feature_names=feature_names,
            class_names=model.classification_labels,
        )
    else:
        raise ValueError(f"Prediction task is not supported: {model.model_type}")
    return explanation_chart_data


@timer()
def explain_text(model: BaseModel, input_df: pd.DataFrame, text_column: str, text_document: str):
    try:
        from shap import Explainer
        from shap.maskers import Text
    except ImportError as e:
        raise GiskardImportError("shap") from e
    try:
        masker = Text(tokenizer=r"\W+")
        text_explainer = Explainer(text_explanation_prediction_wrapper(model.predict_df, input_df, text_column), masker)
        shap_values = text_explainer(pd.Series([text_document]))

        return (
            (shap_values[0].data, [shap_values[0].values[:, i] for i in range(shap_values[0].values.shape[1])])
            if model.is_classification
            else (shap_values[0].data, shap_values[0].values)
        )
    except Exception as e:
        logger.error("Failed to explain text %s", text_document)
        logger.exception(e)
        raise Exception("Failed to create text explanation") from e


def summary_shap_classification(
    shap_values: List[np.ndarray],
    feature_names: List[str],
    class_names: List[str],
    max_display: int = 5,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    feature_order = np.argsort(np.sum(np.mean(np.abs(shap_values), axis=1), axis=0))
    feature_order = feature_order[-min(max_display, len(feature_order)) :]
    feature_inds = feature_order[:max_display]
    chart_data: Dict[str, Dict[Any, Any]] = {"explanations": {}}
    for i in range(len(shap_values)):
        global_shap_values = np.abs(shap_values[i]).mean(0)
        chart_data["explanations"][class_names[i]] = {
            feature_names[feature_ind]: global_shap_values[feature_ind] for feature_ind in feature_inds
        }
    return chart_data


def summary_shap_regression(
    shap_values: np.ndarray, feature_names: List[str], max_display: int = 5
) -> Dict[str, Dict[str, Dict[str, float]]]:
    max_display = min(max_display, shap_values.shape[1])
    feature_order = np.argsort(np.mean(np.abs(shap_values), axis=0))
    feature_order = feature_order[-max_display:]
    feature_inds = feature_order[:max_display]
    global_shap_values = np.abs(shap_values).mean(0)

    chart_data = {
        "explanations": {
            "default": {feature_names[feature_ind]: global_shap_values[feature_ind] for feature_ind in feature_inds}
        }
    }
    return chart_data


def text_explanation_prediction_wrapper(
    prediction_function: Callable, input_example: pd.DataFrame, text_column: str
) -> Callable:
    def text_predict(text_documents: List[str]):
        num_documents = len(text_documents)
        df_with_text_documents = (
            input_example.copy()
            if num_documents == 1
            else pd.concat([input_example] * num_documents, ignore_index=True)
        )
        df_with_text_documents[text_column] = text_documents
        return prediction_function(df_with_text_documents)

    return text_predict
