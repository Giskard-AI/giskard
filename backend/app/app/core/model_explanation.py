from typing import Dict, List, Callable
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


def background_example(df: pd.DataFrame, input_types: Dict[str, str]) -> pd.DataFrame:
    example = df.mode(dropna=False).iloc[[0]]  # si plusieurs modes, on prend le premier
    example.fillna("", inplace=True)
    median = df.median()
    num_columns = [key for key in input_types.keys() if input_types[key] == "numeric"]
    for column in num_columns:
        example[column] = median[column]
    return example


def summary_shap_classification(
    shap_values: List[np.ndarray],
    feature_names: List[str],
    class_names: List[str],
    max_display: int = 5,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    feature_order = np.argsort(np.sum(np.mean(np.abs(shap_values), axis=1), axis=0))
    feature_order = feature_order[-min(max_display, len(feature_order)) :]
    feature_inds = feature_order[:max_display]
    chart_data = {"explanations": {}}
    for i in range(len(shap_values)):
        global_shap_values = np.abs(shap_values[i]).mean(0)
        chart_data["explanations"][class_names[i]] = {
            feature_names[feature_ind]: global_shap_values[feature_ind]
            for feature_ind in feature_inds
        }
    return chart_data


def summary_shap_regression(
    shap_values: List[np.ndarray], feature_names: List[str], max_display: int = 5
) -> Dict[str, Dict[str, float]]:
    feature_order = np.argsort(np.sum(np.mean(np.abs(shap_values), axis=1), axis=0))
    feature_order = feature_order[-min(max_display, len(feature_order)) :]
    feature_inds = feature_order[:max_display]
    global_shap_values = np.abs(shap_values[0]).mean(0)
    chart_data = {"explanations": {}}
    chart_data["explanations"] = {
        feature_names[feature_ind]: global_shap_values[feature_ind] for feature_ind in feature_inds
    }
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
    text_explanation_soup = BeautifulSoup(response, 'html.parser')
    labels = []
    explanations_html = []
    for i, paragraph in enumerate(text_explanation_soup.find_all('p')):
        if (i % 2) == 0:
            label = re.findall(r"\by=.*\b", str(paragraph.find("b")))[0][2:]
            labels.append(label)
        else:
            explanations_html.append(str(paragraph))
    return zip(labels, explanations_html)
