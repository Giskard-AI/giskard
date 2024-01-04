from typing import Optional

from dataclasses import dataclass
from enum import Enum

from giskard.client.python_utils import warning
from giskard.core.core import ModelType, SupportedModelTypes
from giskard.core.errors import GiskardImportError

from ..utils.analytics_collector import analytics


class PanelNames(str, Enum):
    """Enumeration to store WandB UI panel names for different charts."""

    CATEGORICAL = "Feature importance for categorical features"
    NUMERICAL = "Feature importance for numerical features"
    GENERAL = "Global feature importance"


@dataclass
class ShapResult:
    """Dataclass to log the SHAP explanation result.

    Stores the SHAP explanation results and provides the logic to log the SHAP
    charts to the WandB run.

    Parameters
    ----------
    explanations : shap.Explanation
        The SHAP explanations.

    feature_types : dict (optional, default=None)
        Mapping between the features' names and their types.

    model_type : ModelType (optional, default=None)
        Type of the model: classification, regression or text.

    only_highest_proba: bool (default=True)
        A flag indicating whether to provide SHAP explanations only for the predictions with the highest probability or not.
    """

    try:
        from shap import Explanation
    except ImportError as e:
        raise GiskardImportError("shap") from e

    explanations: Explanation
    feature_types: Optional[dict] = None
    model_type: Optional[ModelType] = None
    only_highest_proba: bool = True

    def _validate_wandb_config(self) -> None:
        """Check if the object was initialized correctly to log the SHAP charts."""
        if self.feature_types is None:
            raise ValueError("The attribute 'ShapResult.feature_types' is needed for 'ShapResult.to_wandb()'.")
        if self.only_highest_proba and self.model_type is None:
            raise ValueError("The attribute 'ShapResult.model_type' is needed for 'ShapResult.to_wandb()'.")
        if not self.only_highest_proba and self.model_type == SupportedModelTypes.CLASSIFICATION:
            raise ValueError(
                "We currently support 'ShapResult.to_wandb()' only with 'only_highest_proba == True' for "
                "classification models."
            )

    def to_wandb(self, run: Optional["wandb.wandb_sdk.wandb_run.Run"] = None) -> None:  # noqa
        """Create and log the SHAP charts to the WandB run.

        For the active WandB run, logs SHAP charts, which include:

        - Scatter plot for each numerical feature.
        - Bar plot for each categorical feature.
        - Single Bar plot for the general feature importance.

        Parameters
        ----------
        run :
            WandB run.
        """
        try:
            import wandb  # noqa
        except ImportError as e:
            raise GiskardImportError("wandb") from e
        from ..integrations.wandb.wandb_utils import (
            _wandb_bar_plot,
            _wandb_general_bar_plot,
            _wandb_scatter_plot,
            get_wandb_run,
        )

        run = get_wandb_run(run)
        self._validate_wandb_config()

        try:
            charts = dict()

            # Create general SHAP feature importance plot.
            general_bar_plot = _wandb_general_bar_plot(self.explanations, list(self.feature_types.keys()))
            charts.update({f"{PanelNames.GENERAL}/general_shap_bar_plot": general_bar_plot})

            counter = {"category": 0, "numeric": 0, "text": 0}
            for t in self.feature_types.values():
                counter[t] += 1

            analytics.track(
                "wandb_integration:shap_result:shap_result",
                {
                    "wandb_run_id": run.id,
                    "cat_feat_cnt": counter["category"],
                    "num_feat_cnt": counter["numeric"],
                    "text_feat_cnt": counter["text"],
                },
            )

            # Create per-feature SHAP plots.
            for feature_name, feature_type in self.feature_types.items():
                if feature_type == "category":
                    bar_plot = _wandb_bar_plot(self.explanations, feature_name)
                    charts.update({f"{PanelNames.CATEGORICAL}/{feature_name}_shap_bar_plot": bar_plot})
                elif feature_type == "numeric":
                    scatter_plot = _wandb_scatter_plot(self.explanations, feature_name)
                    charts.update({f"{PanelNames.NUMERICAL}/{feature_name}_shap_scatter_plot": scatter_plot})
                else:
                    warning_msg = (
                        f"We do not support the wandb logging of ShapResult for text features yet. The "
                        f"SHAP plot for '{feature_name}' won't be logged into wandb."
                    )
                    analytics.track(
                        "wandb_integration:shap_result:warning:text_not_supported",
                        {
                            "wandb_run_id": run.id,
                            "warning": str(warning_msg),
                        },
                    )
                    warning(warning_msg)
        except Exception as e:
            analytics.track(
                "wandb_integration:shap_result:error:unknown",
                {
                    "wandb_run_id": run.id,
                    "error": str(e),
                },
            )
            raise RuntimeError(
                "An error occurred while logging the SHAP results into wandb. "
                "Please submit the traceback as a GitHub issue in the following "
                "repository for further assistance: https://github.com/Giskard-AI/giskard."
            ) from e

        # Log created plots.
        run.log(charts)
