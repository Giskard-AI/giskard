from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import AVAILABLE_METRICS, ToolDescription
from giskard.llm.talk.tools.base import BaseTool, PredictionMixin

if TYPE_CHECKING:
    from giskard.models.base import BaseModel


class MetricTool(BaseTool, PredictionMixin):
    """Performance metric calculation Tool.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

    default_name: str = "calculate_metric"
    default_description: str = ToolDescription.CALCULATE_METRIC.value

    def __init__(
        self, model: BaseModel, dataset: Dataset, name: Optional[str] = None, description: Optional[str] = None
    ):
        """Constructor of the class.

        Parameters
        ----------
        model : BaseModel
            The Giskard Model.
        dataset : Dataset
            The Giskard Dataset.
        name : str, optional
            The name of the Tool.
            If not set, the `default_name` is used.
        description : str, optional
            The description of the Tool.
            If not set, the `default_description` is used.
        """
        BaseTool.__init__(self, name, description)
        PredictionMixin.__init__(self, model, dataset)

    @property
    def specification(self) -> str:
        """Return the Tool's specification in a JSON Schema format.

        Returns
        -------
        str
            The Tool's specification.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_type": {"type": "string", "enum": list(AVAILABLE_METRICS.keys())},
                        "features_dict": {
                            "type": "object",
                            "properties": {
                                feature: {"type": dtype} for feature, dtype in self.features_json_type.items()
                            },
                        },
                    },
                    "required": ["metric_type", "features_dict"],
                },
            },
        }

    def __call__(self, metric_type: str, features_dict: dict[str, any]) -> str:
        """Execute the Tool's functionality.

        Calculate the given performance metric on rows from the dataset.

        Parameters
        ----------
        metric_type : str
            The type of the performance metric to calculate.
        features_dict : dict[str, any]
            The dictionary with features and related values to filter the dataset.

        Returns
        -------
        str
            The calculated performance metric.
        """

        self._validate_features_dict(features_dict)

        # Get the predicted labels.
        model_input = self._get_input_from_dataset(features_dict)
        model_input = Dataset(model_input, target=self._dataset.target)
        if len(model_input) == 0:
            raise ValueError("No records found in the dataset for the given combination of feature values.")

        # Calculate the metric value.
        # Temporary workaround, unless we solve the circular import error, when importing performance at the top level.
        from giskard.testing.tests import performance

        metric = getattr(performance, AVAILABLE_METRICS[metric_type])
        metric_value = metric(self._model, model_input).execute()
        return str(metric_value)
