import logging
import warnings
from typing import Callable, Dict, List, Any, Tuple, Iterable

import wandb
import numpy as np
import pandas as pd

from giskard.datasets.base import Dataset
from giskard.ml_worker.utils.logging import timer
from giskard.models.base import BaseModel

warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")
import shap  # noqa

logger = logging.getLogger(__name__)


def explain_full(model: BaseModel, dataset: Dataset, input_data: pd.DataFrame) -> Tuple[np.ndarray, shap.Explainer]:
    """Perform SHAP values calculation for each sample of a given dataset."""

    def prepare_df(_df):
        _df = model.prepare_dataframe(_df, column_dtypes=dataset.column_dtypes, target=dataset.target)

        if dataset.target in _df.columns:
            prepared_dataset = Dataset(_df, target=dataset.target, column_types=dataset.column_types)
        else:
            prepared_dataset = Dataset(_df, column_types=dataset.column_types)

        prepared_df = prepared_dataset.df

        columns_original_order = (
            model.meta.feature_names
            if model.meta.feature_names
            else [c for c in dataset.df.columns if c in prepared_df.columns]
        )

        # Make sure column order is the same as in df.
        return prepared_df[columns_original_order]

    # Prepare background sample to be used in the KernelSHAP.
    background_df = model.prepare_dataframe(dataset.df, dataset.column_dtypes, dataset.target)
    background_sample = background_example(background_df, dataset.column_types)

    # Prepare input data for explanation.
    input_df = prepare_df(input_data)

    # Obtain SHAP explanations.
    explainer = shap.KernelExplainer(
        model.predict_df, background_sample, keep_index=True, feature_names=input_df.columns
    )
    shap_values = explainer.shap_values(input_df, silent=True)

    return shap_values, explainer


def _get_cls_prediction_explanation(model: BaseModel, dataset: Dataset, shap_values: list):
    # Get raw indices of predictions with the highest probability.
    predictions = model.predict(dataset).raw_prediction

    # Select SHAP values, which explain model's predictions with the highest probability.
    filtered_shap_values = list()

    for sample_idx, sample_prediction_idx in enumerate(predictions):
        prediction_explanation = shap_values[sample_prediction_idx][sample_idx]
        filtered_shap_values.append(prediction_explanation)

    return filtered_shap_values


def _wandb_bar_plot(shap_explanations: shap.Explanation, feature_name: str):
    """Get wandb bar plot of shap values of the categorical feature."""
    _FEATURE_COLUMN = "feature_values"
    _SHAP_COLUMN = "shap_abs_values"

    # Extract feature values and related shap explanations.
    shap_values = shap_explanations[:, feature_name].values
    feature_values = shap_explanations[:, feature_name].data

    # We are interested in magnitude.
    shap_abs_values = np.abs(shap_values)

    # Calculate mean shap value per feature value.
    df = pd.DataFrame(data={_FEATURE_COLUMN: feature_values, _SHAP_COLUMN: shap_abs_values})
    shap_abs_means = pd.DataFrame(df.groupby(_FEATURE_COLUMN)[_SHAP_COLUMN].mean()).reset_index()

    # Create bar plot.
    table = wandb.Table(dataframe=shap_abs_means)
    plot = wandb.plot.bar(
        table, label=_FEATURE_COLUMN, value=_SHAP_COLUMN, title=f"Mean(Abs(SHAP)) of '{feature_name}' feature values"
    )

    return plot


def _wandb_scatter_plot(shap_explanations: shap.Explanation, feature_name: str):
    """Get wandb scatter plot of shap values of the numerical feature."""
    _FEATURE_COLUMN = "feature_values"
    _SHAP_COLUMN = "shap_values"

    # Extract feature values and related shap explanations.
    shap_values = shap_explanations[:, feature_name].values
    feature_values = shap_explanations[:, feature_name].data

    # Create scatter plot.
    df = pd.DataFrame(data={_FEATURE_COLUMN: feature_values, _SHAP_COLUMN: shap_values})
    table = wandb.Table(dataframe=df)
    plot = wandb.plot.scatter(
        table, y=_FEATURE_COLUMN, x=_SHAP_COLUMN, title=f"'{feature_name}' feature values vs SHAP values"
    )

    return plot


def _wandb_general_bar_plot(shap_explanations: shap.Explanation, feature_names: Iterable):
    """Get wandb bar plot of general shap mean values."""
    _FEATURE_COLUMN = "feature"
    _SHAP_COLUMN = "global_shap_mean"

    # Calculate global shap means.
    shap_general_means = list()

    for feature_name in feature_names:
        shap_general_means.append(np.abs(shap_explanations[:, feature_name].values).mean())

    # Create bar plot.
    df = pd.DataFrame(data={_FEATURE_COLUMN: feature_names, _SHAP_COLUMN: shap_general_means})
    table = wandb.Table(dataframe=df)
    plot = wandb.plot.bar(
        table, label=_FEATURE_COLUMN, value=_SHAP_COLUMN, title="General Mean(Abs(SHAP)) across all features"
    )

    return plot


def shap_to_wandb(model: BaseModel, dataset: Dataset, **kwargs) -> None:
    """Log SHAP explanation graphs to the WandB run."""
    from giskard.integrations.wandb.wandb_utils import wandb_run

    with wandb_run(**kwargs) as run:
        _FEATURE_NAMES = model.meta.feature_names or list(dataset.df.columns.drop(dataset.target, errors="ignore"))
        _FEATURE_TYPES = {key: dataset.column_types[key] for key in _FEATURE_NAMES}

        # Calculate SHAP values.
        shap_values, explainer = explain_full(model, dataset, dataset.df)

        # For classification, take SHAP of prediction with the highest probability.
        if model.is_classification:
            shap_values = _get_cls_prediction_explanation(model, dataset, shap_values)

        # Put shap and feature names to the Explanation object for a convenience.
        shap_explanations = shap.Explanation(
            values=shap_values, data=dataset.df[_FEATURE_NAMES], feature_names=_FEATURE_NAMES
        )

        # Create and log plots to the wandb run.
        log_plots_dict = dict()

        for feature_name, feature_type in _FEATURE_TYPES.items():
            if feature_type == "category":
                bar_plot = _wandb_bar_plot(shap_explanations, feature_name)
                log_plots_dict.update(
                    {f"Feature importance for categorical features/{feature_name}_shap_bar_plot": bar_plot}
                )
            elif feature_type == "numeric":
                scatter_plot = _wandb_scatter_plot(shap_explanations, feature_name)
                log_plots_dict.update(
                    {f"Feature importance for numerical features/{feature_name}_shap_scatter_plot": scatter_plot}
                )
            else:
                raise NotImplementedError("We do not support the SHAP logging of text features yet.")

        general_bar_plot = _wandb_general_bar_plot(shap_explanations, _FEATURE_NAMES)
        log_plots_dict.update({"Global feature importance/general_shap_bar_plot": general_bar_plot})
        run.log(log_plots_dict)


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
