from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BasePredictTool


class PredictDatasetInputTool(BasePredictTool):
    default_name: str = "predict_dataset_input"
    default_description: str = ToolDescription.PREDICT_DATASET_INPUT.value

    def _prepare_input(self, row_filter: dict) -> Dataset:
        filtered_df = self._dataset.df.copy()
        for col_name, col_value in list(row_filter.items()):
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[filtered_df[col_name].str.lower() == str(col_value).lower()]
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df, target=None)


class PredictUserInputTool(BasePredictTool):
    default_name: str = "predict_user_input"
    default_description: str = ToolDescription.PREDICT_USER_INPUT.value

    def _prepare_input(self, feature_values: dict) -> Dataset:
        # Prepare background sample.
        from giskard.models.model_explanation import _get_background_example

        background_df = self._model.prepare_dataframe(
            self._dataset.df, self._dataset.column_dtypes, self._dataset.target
        )
        background_sample = _get_background_example(background_df, self._dataset.column_types)

        # Fill background sample with known values.
        for col_name, col_value in list(feature_values.items()):
            background_sample.loc[0, col_name] = col_value

        return Dataset(background_sample, target=None)
