import logging
import warnings
from typing import Callable, Dict, List, Any

import numpy as np
import pandas as pd
from shap.maskers import Text
from shap import KernelExplainer, Explanation, Explainer

from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel
from giskard.models.shap_result import ShapResult
from giskard.ml_worker.utils.logging import timer

warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")
logger = logging.getLogger(__name__)


def _get_highest_prob_shap(model: BaseModel, dataset: Dataset, shap_values: list) -> list:
    """Get SHAP explanations of classes with the highest predicted probability."""
    predictions = model.predict(dataset).raw_prediction
    return [shap_values[predicted_class][sample_idx] for sample_idx, predicted_class in enumerate(predictions)]


def prepare_df(df: pd.DataFrame, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
    """Prepare dataframe for an inference step."""
    df = model.prepare_dataframe(df, column_dtypes=dataset.column_dtypes, target=dataset.target)

    if dataset.target in df.columns:
        prepared_dataset = Dataset(df, column_types=dataset.column_types, target=dataset.target)
    else:
        prepared_dataset = Dataset(df, column_types=dataset.column_types)

    # Make sure column order is the same as in the dataset.df.
    columns_original_order = (
        model.meta.feature_names
        if model.meta.feature_names
        else [c for c in dataset.df.columns if c in prepared_dataset.df.columns]
    )

    prepared_df = prepared_dataset.df[columns_original_order]
    return prepared_df


def background_example(df: pd.DataFrame, input_types: Dict[str, str]) -> pd.DataFrame:
    """Create back-ground example for the SHAP explainer as a mode/median of features of the data to explain."""
    median = df.median()
    example = df.mode(dropna=False).head(1)
    num_columns = [key for key in list(df.columns) if input_types.get(key) == "numeric"]

    # Replace a numerical features' mode on their median.
    for column in num_columns:
        example[column] = median[column]

    example = example.astype(df.dtypes)
    return example


def explain_full(model: BaseModel, dataset: Dataset) -> np.ndarray:
    """Perform SHAP values calculation for samples of a given dataset."""
    # Prepare background sample to be used in the KernelSHAP.
    background_df = model.prepare_dataframe(dataset.df, dataset.column_dtypes, dataset.target)
    background_sample = background_example(background_df, dataset.column_types)

    # Prepare input data for explanation.
    input_df = prepare_df(dataset.df, model=model, dataset=dataset)

    # Obtain SHAP explanations.
    explainer = KernelExplainer(model.predict_df, background_sample, feature_names=input_df.columns, keep_index=True)
    shap_values = explainer.shap_values(input_df, silent=True)
    return shap_values


def explain_with_shap(model: BaseModel, dataset: Dataset) -> ShapResult:
    """Get SHAP explanation result."""
    # Obtain SHAP explanations.
    shap_values = explain_full(model, dataset)

    # For classification, take SHAP of prediction with the highest probability.
    if model.is_classification:
        shap_values = _get_highest_prob_shap(model, dataset, shap_values)

    # Put shap and feature names to the Explanation object for a convenience.
    feature_names = model.meta.feature_names or list(dataset.df.columns.drop(dataset.target, errors="ignore"))
    feature_types = {key: dataset.column_types[key] for key in feature_names}
    shap_explanations = Explanation(values=shap_values, data=dataset.df[feature_names], feature_names=feature_names)
    return ShapResult(shap_explanations, feature_types, feature_names)


def explain_one(model: BaseModel, dataset: Dataset, input_data: Dict) -> np.ndarray:
    df = model.prepare_dataframe(dataset.df, column_dtypes=dataset.column_dtypes, target=dataset.target)
    input_df = prepare_df(pd.DataFrame([input_data]), model=model, dataset=dataset)

    def predict_array(array):
        arr_df = pd.DataFrame(array, columns=list(df.columns))
        return model.predict_df(prepare_df(arr_df, model=model, dataset=dataset))

    example = background_example(df, dataset.column_types)
    kernel = KernelExplainer(predict_array, example)
    shap_values = kernel.shap_values(input_df, silent=True)
    return shap_values


@timer()
def explain(model: BaseModel, dataset: Dataset, input_data: Dict):
    shap_values = explain_one(model, dataset, input_data)
    feature_names = model.meta.feature_names or list(dataset.df.columns.drop(dataset.target, errors="ignore"))

    if model.is_regression:
        explanation_chart_data = summary_shap_regression(shap_values=shap_values, feature_names=feature_names)
    elif model.is_classification:
        explanation_chart_data = summary_shap_classification(
            shap_values=shap_values,
            feature_names=feature_names,
            class_names=model.meta.classification_labels,
        )
    else:
        raise ValueError(f"Prediction task is not supported: {model.meta.model_type}")
    return explanation_chart_data


@timer()
def explain_text(model: BaseModel, input_df: pd.DataFrame, text_column: str, text_document: str):
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
        logger.exception(f"Failed to explain text: {text_document}", e)
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

        df_with_text_documents = input_example.append([input_example] * (num_documents - 1), ignore_index=True)
        df_with_text_documents[text_column] = pd.DataFrame(text_documents)
        return prediction_function(df_with_text_documents)

    return text_predict
