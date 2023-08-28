from enum import Enum
from dataclasses import dataclass
from typing import Optional

from shap import Explanation

from giskard.core.core import ModelType, SupportedModelTypes
from ..utils.analytics_collector import analytics
from giskard.client.python_utils import warning


class PanelNames(str, Enum):
    CATEGORICAL = "Feature importance for categorical features"
    NUMERICAL = "Feature importance for numerical features"
    GENERAL = "Global feature importance"


@dataclass
class ShapResult:
    explanations: Explanation
    feature_types: Optional[dict] = None
    model_type: Optional[ModelType] = None
    only_highest_proba: bool = True

    def _validate_wandb_config(self):
        if self.feature_types is None:
            raise ValueError("The attribute 'ShapResult.feature_types' is needed for 'ShapResult.to_wandb()'.")
        if self.only_highest_proba and self.model_type is None:
            raise ValueError("The attribute 'ShapResult.model_type' is needed for 'ShapResult.to_wandb()'.")
        if not self.only_highest_proba and self.model_type == SupportedModelTypes.CLASSIFICATION:
            raise ValueError(
                "We currently support 'ShapResult.to_wandb()' only with 'only_highest_proba == True' for "
                "classification models."
            )

    def to_wandb(self, **kwargs) -> None:
        """Create and log to the WandB run SHAP charts."""
        from giskard.integrations.wandb.wandb_utils import wandb_run
        from giskard.integrations.wandb.wandb_utils import _wandb_bar_plot, _wandb_general_bar_plot, _wandb_scatter_plot

        self._validate_wandb_config()

        with wandb_run(**kwargs) as run:
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
                raise ValueError(
                    "An error occurred while logging the SHAP results into wandb. "
                    "Please submit the traceback as a GitHub issue in the following "
                    "repository for further assistance: https://github.com/Giskard-AI/giskard."
                ) from e

            # Log created plots.
            run.log(charts)
