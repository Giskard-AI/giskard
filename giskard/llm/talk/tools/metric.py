from thefuzz import fuzz

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import AVAILABLE_METRICS, ToolDescription
from giskard.llm.talk.tools.base import BaseTool, get_feature_json_type


class MetricTool(BaseTool):
    default_name: str = "calculate_metric"
    default_description: str = ToolDescription.CALCULATE_METRIC.value

    @property
    def specification(self) -> str:
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
                            "properties": {
                                feature: {"type": dtype} for feature, dtype in list(feature_json_type.items())
                            },
                        },
                    },
                    "required": ["metric_type", "features_dict"],
                },
            },
        }

    def _get_input_from_dataset(self, row_filter: dict) -> Dataset:
        threshold = 85

        filtered_df = self._dataset.df.copy()
        for col_name, col_value in list(row_filter.items()):
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[
                    filtered_df[col_name].apply(lambda x: fuzz.ratio(x.lower(), col_value.lower()) >= threshold)
                ]
                if not filtered_df:
                    break
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df, target=None)

    def __call__(self, metric_type: str, features_dict: dict) -> str:
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
