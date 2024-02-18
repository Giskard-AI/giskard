from thefuzz import fuzz

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import AVAILABLE_METRICS, ToolDescription
from giskard.llm.talk.tools.base import BaseTool


class MetricTool(BaseTool):
    default_name: str = "calculate_metric"
    default_description: str = ToolDescription.CALCULATE_METRIC.value

    def _get_feature_json_type(self) -> dict[any, str]:
        number_columns = {column: "number" for column in self._dataset.df.select_dtypes(include=(int, float)).columns}
        string_columns = {column: "string" for column in self._dataset.df.select_dtypes(exclude=(int, float)).columns}
        return number_columns | string_columns

    @property
    def specification(self) -> str:
        feature_json_type = self._get_feature_json_type()

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

    def _filter_from_dataset(self, row_filter: dict) -> Dataset:
        threshold = 85

        filtered_df = self._dataset.df.copy()
        for col_name, col_value in list(row_filter.items()):
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[
                    filtered_df[col_name].apply(lambda x: fuzz.ratio(x.lower(), col_value.lower()) >= threshold)
                ]
                if not len(filtered_df):
                    break
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df, target=None)

    def __call__(self, metric_type: str, features_dict: dict) -> str:
        # Get the predicted labels.
        model_input = self._filter_from_dataset(features_dict)
        prediction = self._model.predict(model_input).prediction

        # Get the ground-truth labels.
        ground_truth = self._dataset.df[self._dataset.target]

        # Calculate the metric value.
        metric = AVAILABLE_METRICS[metric_type]
        metric_score = metric(ground_truth, prediction)
        return str(metric_score)
