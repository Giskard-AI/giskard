import pandas as pd
from thefuzz import fuzz

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BaseTool, get_feature_json_type


class PredictTool(BaseTool):
    default_name: str = "predict"
    default_description: str = ToolDescription.PREDICT.value

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
                        "features_dict": {
                            "type": "object",
                            "properties": {
                                feature: {"type": dtype} for feature, dtype in list(feature_json_type.items())
                            },
                        }
                    },
                    "required": ["features_dict"],
                },
            },
        }

    def _get_input_from_dataset(self, row_filter: dict) -> pd.DataFrame:
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

        return filtered_df

    def _get_input_from_user(self, feature_values: dict) -> pd.DataFrame:
        # Prepare background sample.
        from giskard.models.model_explanation import _get_background_example

        background_df = self._model.prepare_dataframe(
            self._dataset.df, self._dataset.column_dtypes, self._dataset.target
        )
        background_sample = _get_background_example(background_df, self._dataset.column_types)

        # Fill background sample with known values.
        for col_name, col_value in list(feature_values.items()):
            background_sample.loc[0, col_name] = col_value

        return background_sample

    def _prepare_input(self, feature_values: dict) -> Dataset:
        final_input = self._get_input_from_dataset(feature_values)

        # If no data were filtered from the dataset, build vector from the user input.
        if len(final_input) == 0:
            final_input = self._get_input_from_user(feature_values)

        return Dataset(final_input, target=None)

    def __call__(self, features_dict: dict) -> str:
        model_input = self._prepare_input(features_dict)
        prediction = self._model.predict(model_input).prediction
        return ", ".join(map(str, prediction))
