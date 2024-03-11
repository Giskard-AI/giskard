from difflib import SequenceMatcher as SeqM

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import AVAILABLE_METRICS, FUZZY_SIMILARITY_THRESHOLD, ToolDescription
from giskard.llm.talk.tools.base import BaseTool, get_feature_json_type


class MetricTool(BaseTool):
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

    @property
    def specification(self) -> str:
        """Return the Tool's specification in a JSON Schema format.

        Returns
        -------
        str
            The Tool's specification.
        """
        feature_json_type = get_feature_json_type(self._dataset)

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
                            "properties": {feature: {"type": dtype} for feature, dtype in feature_json_type.items()},
                        },
                    },
                    "required": ["metric_type", "features_dict"],
                },
            },
        }

    def _get_input_from_dataset(self, row_filter: dict[str, any]) -> Dataset:
        """Get input from dataset.

        Filter rows from the dataset, using the `row_filter`.

        Parameters
        ----------
        row_filter : dict[str, any]
            The dictionary with features and related values to filter the dataset.

        Returns
        -------
        Dataset
            The Giskard Dataset with filtered rows.
        """
        filtered_df = self._dataset.df
        for col_name, col_value in row_filter.items():
            # Use fuzzy comparison to filter string features.
            if filtered_df[col_name].dtype == "object":
                index = filtered_df[col_name].apply(
                    lambda x: SeqM(None, x.lower(), col_value.lower()).ratio() >= FUZZY_SIMILARITY_THRESHOLD
                )
            else:
                # Otherwise, filter by the exact value.
                index = filtered_df[col_name] == col_value

            # Apply selection.
            filtered_df = filtered_df[index]

            # Break, if dataframe is empty.
            if not len(filtered_df):
                break

        return Dataset(filtered_df, target=None)

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
        # Get the predicted labels.
        model_input = self._get_input_from_dataset(features_dict)
        if len(model_input) == 0:
            raise ValueError("No records in the dataset given feature values combination.")

        prediction = self._model.predict(model_input).prediction

        # Get the ground-truth labels.
        ground_truth = model_input.df[self._dataset.target]

        # Calculate the metric value.
        metric = AVAILABLE_METRICS[metric_type]
        metric_value = metric(ground_truth, prediction)
        return str(metric_value)
