import logging
import re
from typing import Callable, Dict, List, Any

import numpy as np
import pandas as pd
import shap
from bs4 import BeautifulSoup
from eli5.lime import TextExplainer

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel
from giskard.ml_worker.utils.logging import timer

logger = logging.getLogger(__name__)


@timer()
def explain(model: GiskardModel, dataset: GiskardDataset, input_data: Dict):
    def prepare_df(df):
        return model.prepare_dataframe(
            GiskardDataset(
                df=df,
                target=dataset.target,
                feature_types=dataset.feature_types,
                column_types=dataset.column_types,
            )
        )

    df = model.prepare_dataframe(dataset)
    feature_names = list(df.columns)

    # Make sure column order is that column order is the same as in df
    input_data_df = pd.DataFrame([input_data])[df.columns]
    input_df = prepare_df(input_data_df)

    def predict_array(array):
        return model.prediction_function(prepare_df(pd.DataFrame(array, columns=list(df.columns))))

    example = background_example(df, dataset.feature_types)
    kernel = shap.KernelExplainer(predict_array, example)
    shap_values = kernel.shap_values(input_df)

    if model.model_type == "regression":
        explanation_chart_data = summary_shap_regression(
            shap_values=shap_values, feature_names=feature_names
        )
    elif model.model_type == "classification":
        explanation_chart_data = summary_shap_classification(
            shap_values=shap_values,
            feature_names=feature_names,
            class_names=model.classification_labels,
        )
    else:
        raise ValueError(f"Prediction task is not supported: {model.model_type}")
    return explanation_chart_data


@timer()
def explain_text(model: GiskardModel, input_df: pd.DataFrame,
                 text_column: str, text_document: str, n_samples: int):
    text_explainer = TextExplainer(random_state=42, n_samples=n_samples)
    prediction_function = text_explanation_prediction_wrapper(
        model.prediction_function, input_df, text_column
    )
    try:
        text_explainer.fit(text_document, prediction_function)
        return text_explainer.show_prediction(target_names=model.classification_labels)
    except Exception as e:
        logger.exception(f"Failed to explain text: {text_document}", e)
        raise Exception("Failed to create text explanation") from e


def background_example(df: pd.DataFrame, input_types: Dict[str, str]) -> pd.DataFrame:
    example = df.mode(dropna=False).head(1)  # si plusieurs modes, on prend le premier
    example.fillna("", inplace=True)
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
    feature_order = feature_order[-min(max_display, len(feature_order)):]
    feature_inds = feature_order[:max_display]
    chart_data: Dict[str, Dict[Any, Any]] = {"explanations": {}}
    for i in range(len(shap_values)):
        global_shap_values = np.abs(shap_values[i]).mean(0)
        chart_data["explanations"][class_names[i]] = {
            feature_names[feature_ind]: global_shap_values[feature_ind]
            for feature_ind in feature_inds
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

    chart_data = {"explanations": {
        "default": {
            feature_names[feature_ind]: global_shap_values[feature_ind]
            for feature_ind in feature_inds
        }
    }}
    return chart_data


def text_explanation_prediction_wrapper(
        prediction_function: Callable, input_example: pd.DataFrame, text_column: str
) -> Callable:
    def text_predict(text_documents: List[str]):
        num_documents = len(text_documents)
        df_with_text_documents = input_example.append(
            [input_example] * (num_documents - 1), ignore_index=True
        )
        df_with_text_documents[text_column] = pd.DataFrame(text_documents)
        return prediction_function(df_with_text_documents)

    return text_predict


def parse_text_explainer_response(response: str) -> Dict[str, str]:
    text_explanation_soup = BeautifulSoup(response, "html.parser")
    labels = []
    explanations_html = []
    for i, paragraph in enumerate(text_explanation_soup.find_all("p")):
        if (i % 2) == 0:
            label = re.findall(r"\by=.*\b", str(paragraph.find("b")))[0][2:]
            labels.append(label)
        else:
            explanations_html.append(str(paragraph))
    return dict(zip(labels, explanations_html))
