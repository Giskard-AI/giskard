from typing import Any, Iterable
from dataclasses import dataclass

import wandb
import numpy as np
import pandas as pd
from shap import Explanation


def _wandb_bar_plot(shap_explanations: Explanation, feature_name: str) -> Any:
    """Get wandb bar plot of shap values of the categorical feature."""
    feature_column = "feature_values"
    shap_column = "shap_abs_values"

    # Extract feature values and related shap explanations.
    shap_values = shap_explanations[:, feature_name].values
    feature_values = shap_explanations[:, feature_name].data

    # We are interested in magnitude.
    shap_abs_values = np.abs(shap_values)

    # Calculate mean shap value per feature value.
    df = pd.DataFrame(data={feature_column: feature_values, shap_column: shap_abs_values})
    shap_abs_means = pd.DataFrame(df.groupby(feature_column)[shap_column].mean()).reset_index()

    # Create bar plot.
    table = wandb.Table(dataframe=shap_abs_means)
    plot = wandb.plot.bar(
        table, label=feature_column, value=shap_column, title=f"Mean(Abs(SHAP)) of '{feature_name}' feature values"
    )

    return plot


def _wandb_scatter_plot(shap_explanations: Explanation, feature_name: str) -> Any:
    """Get wandb scatter plot of shap values of the numerical feature."""
    feature_column = "feature_values"
    shap_column = "shap_values"

    # Extract feature values and related shap explanations.
    shap_values = shap_explanations[:, feature_name].values
    feature_values = shap_explanations[:, feature_name].data

    # Create scatter plot.
    df = pd.DataFrame(data={feature_column: feature_values, shap_column: shap_values})
    table = wandb.Table(dataframe=df)
    plot = wandb.plot.scatter(
        table, y=feature_column, x=shap_column, title=f"'{feature_name}' feature values vs SHAP values"
    )

    return plot


def _wandb_general_bar_plot(shap_explanations: Explanation, feature_names: Iterable) -> Any:
    """Get wandb bar plot of general shap mean values."""
    feature_column = "feature"
    shap_column = "global_shap_mean"

    # Calculate global shap means.
    shap_general_means = list()

    for feature_name in feature_names:
        shap_general_means.append(np.abs(shap_explanations[:, feature_name].values).mean())

    # Create bar plot.
    df = pd.DataFrame(data={feature_column: feature_names, shap_column: shap_general_means})
    table = wandb.Table(dataframe=df)
    plot = wandb.plot.bar(
        table, label=feature_column, value=shap_column, title="General Mean(Abs(SHAP)) across all features"
    )

    return plot


@dataclass
class ShapResult:
    explanations: Explanation = None
    feature_types: dict = None
    feature_names: list = None

    def to_wandb(self, **kwargs) -> None:
        from giskard.integrations.wandb.wandb_utils import wandb_run

        with wandb_run(**kwargs) as run:
            # Create and log plots to the wandb run.
            log_plots_dict = dict()

            for feature_name, feature_type in self.feature_types.items():
                if feature_type == "category":
                    bar_plot = _wandb_bar_plot(self.explanations, feature_name)
                    log_plots_dict.update(
                        {f"Feature importance for categorical features/{feature_name}_shap_bar_plot": bar_plot}
                    )
                elif feature_type == "numeric":
                    scatter_plot = _wandb_scatter_plot(self.explanations, feature_name)
                    log_plots_dict.update(
                        {f"Feature importance for numerical features/{feature_name}_shap_scatter_plot": scatter_plot}
                    )
                else:
                    raise NotImplementedError("We do not support the SHAP logging of text features yet.")

            general_bar_plot = _wandb_general_bar_plot(self.explanations, self.feature_names)
            log_plots_dict.update({"Global feature importance/general_shap_bar_plot": general_bar_plot})
            run.log(log_plots_dict)
