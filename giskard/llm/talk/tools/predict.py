import pandas as pd

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BasePredictTool


class PredictTool(BasePredictTool):
    default_name: str = "predict"
    default_description: str = ToolDescription.PREDICT.value

    def _filter_from_dataset(self, row_filter: dict) -> pd.DataFrame:
        filtered_df = self._dataset.df.copy()
        for col_name, col_value in list(row_filter.items()):
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[filtered_df[col_name].str.lower() == str(col_value).lower()]
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return filtered_df

    def _build_from_user_input(self, feature_values: dict) -> pd.DataFrame:
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
        final_input = self._filter_from_dataset(feature_values)

        # If no data were filtered from the dataset, build vector from the user input.
        if len(final_input) == 0:
            final_input = self._build_from_user_input(feature_values)

        return Dataset(final_input, target=None)
