import logging
import warnings
from typing import Callable, Dict, List, Any

import numpy as np
import pandas as pd

from giskard.datasets.base import Dataset
from giskard.ml_worker.utils.logging import timer
from giskard.models.base import BaseModel

warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")
import shap  # noqa

logger = logging.getLogger(__name__)


@timer()
def explain(model: BaseModel, dataset: Dataset, input_data: Dict):
    def prepare_df(df):
        df = model.prepare_dataframe(df, column_dtypes=dataset.column_dtypes, target=dataset.target)
        if dataset.target in df.columns:
            prepared_ds = Dataset(df=df, target=dataset.target, column_types=dataset.column_types)
        else:
            prepared_ds = Dataset(df=df, column_types=dataset.column_types)
        prepared_df = model.prepare_dataframe(
            prepared_ds.df, column_dtypes=prepared_ds.column_dtypes, target=prepared_ds.target
        )
        columns_in_original_order = (
            model.meta.feature_names
            if model.meta.feature_names
            else [c for c in dataset.df.columns if c in prepared_df.columns]
        )
        # Make sure column order is the same as in df
        return prepared_df[columns_in_original_order]

    df = model.prepare_dataframe(dataset.df, column_dtypes=dataset.column_dtypes, target=dataset.target)
    feature_names = list(df.columns)

    input_df = prepare_df(pd.DataFrame([input_data]))

    def predict_array(array):
        arr_df = pd.DataFrame(array, columns=list(df.columns))
        return model.predict_df(prepare_df(arr_df))

    example = background_example(df, dataset.column_types)
    kernel = shap.KernelExplainer(predict_array, example)
    shap_values = kernel.shap_values(input_df, silent=True)

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
        text_explainer = shap.Explainer(
            text_explanation_prediction_wrapper(model.predict_df, input_df, text_column),
            shap.maskers.Text(tokenizer=r"\W+"),
        )

        shap_values = text_explainer(pd.Series([text_document]))

        return (
            (shap_values[0].data, [shap_values[0].values[:, i] for i in range(shap_values[0].values.shape[1])])
            if model.is_classification
            else (shap_values[0].data, shap_values[0].values)
        )
    except Exception as e:
        logger.exception(f"Failed to explain text: {text_document}", e)
        raise Exception("Failed to create text explanation") from e


def background_example(df: pd.DataFrame, input_types: Dict[str, str]) -> pd.DataFrame:
    example = df.mode(dropna=False).head(1)  # si plusieurs modes, on prend le premier
    # example.fillna("", inplace=True)
    median = df.median()
    num_columns = [key for key in list(df.columns) if input_types.get(key) == "numeric"]
    for column in num_columns:
        example[column] = median[column]
    return example.astype(df.dtypes)


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
