import contextlib
from typing import Optional, Tuple, Generator, Any, Iterable

import numpy as np
import pandas as pd
from shap import Explanation

try:
    import wandb  # noqa
    from wandb.wandb_run import Run
except ImportError as e:
    raise ImportError("The 'wandb' python package is not installed. To get it, run 'pip install wandb'.") from e


@contextlib.contextmanager
def wandb_run(project: Optional[str] = None, **kwargs) -> Generator[Run, None, None]:
    wandb.run = wandb.run or wandb.init(project=project or "giskard", **kwargs)
    wandb.run._label(repo="Giskard")  # noqa
    yield wandb.run


def _parse_test_name(test_name: str) -> Tuple[str, str]:
    """[Temporary] Get a metric and a data slice from a test name."""
    test_name = test_name.split("on data slice")
    metric_name, data_slice = test_name[0], test_name[-1]
    data_slice = data_slice.replace('"', "")
    return metric_name, data_slice


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
