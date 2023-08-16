from enum import Enum
from dataclasses import dataclass

from shap import Explanation

from giskard.core.core import ModelType, SupportedModelTypes


class PanelNames(str, Enum):
    CATEGORICAL = "Feature importance for categorical features"
    NUMERICAL = "Feature importance for numerical features"
    GENERAL = "Global feature importance"


@dataclass
class ShapResult:
    explanations: Explanation = None
    feature_types: dict = None
    feature_names: list = None
    model_type: ModelType = None
    only_highest_proba: bool = True

    def _validate_wandb_config(self):
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
            charts = dict()

            # Create general SHAP feature importance plot.
            general_bar_plot = _wandb_general_bar_plot(self.explanations, self.feature_names)
            charts.update({f"{PanelNames.GENERAL}/general_shap_bar_plot": general_bar_plot})

            # Create per-feature SHAP plots.
            for feature_name, feature_type in self.feature_types.items():
                if feature_type == "category":
                    bar_plot = _wandb_bar_plot(self.explanations, feature_name)
                    charts.update({f"{PanelNames.CATEGORICAL}/{feature_name}_shap_bar_plot": bar_plot})
                elif feature_type == "numeric":
                    scatter_plot = _wandb_scatter_plot(self.explanations, feature_name)
                    charts.update({f"{PanelNames.NUMERICAL}/{feature_name}_shap_scatter_plot": scatter_plot})
                else:
                    raise NotImplementedError(
                        "We do not support the wandb logging of ShapResult for text features yet."
                    )

            # Log created plots.
            run.log(charts)
