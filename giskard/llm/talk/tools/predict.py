from difflib import SequenceMatcher as SeqM

import pandas as pd

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BaseTool, get_feature_json_type


class PredictTool(BaseTool):
    """Prediction calculation Tool.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

    default_name: str = "predict"
    default_description: str = ToolDescription.PREDICT.value

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
        """Get input from dataset.

        Filter rows from the dataset, using the `row_filter`.

        Parameters
        ----------
        row_filter : dict
            The dictionary with features and related values to filter the dataset.

        Returns
        -------
        pd.DataFrame
            The DataFrame with filtered rows.
        """
        threshold = 0.85
        filtered_df = self._dataset.df
        for col_name, col_value in row_filter.items():
            # Use fuzzy comparison to filter string features.
            if filtered_df[col_name].dtype == "object":
                index = filtered_df[col_name].apply(
                    lambda x: SeqM(None, x.lower(), col_value.lower()).ratio() >= threshold
                )
            else:
                # Otherwise, filter by the exact value.
                index = filtered_df[col_name] == col_value

            # Apply selection.
            filtered_df = filtered_df[index]

            # Break, if dataframe is empty.
            if not len(filtered_df):
                break

        return filtered_df

    def _get_input_from_user(self, feature_values: dict) -> pd.DataFrame:
        """Form input based on the user's query.

        Take input feature values from user query. For the missed values, take the feature mean from the Dataset.

        Parameters
        ----------
        feature_values : dict
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        pd.DataFrame
            The DataFrame with the formed input.
        """
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
        """Prepare model input.

        Either extract rows form the dataset, or create input from the user's query.

        Parameters
        ----------
        feature_values : dict
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        Dataset
            The Giskard Dataset with model input.
        """
        final_input = self._get_input_from_dataset(feature_values)

        # If no data were filtered from the dataset, build vector from the user input.
        if len(final_input) == 0:
            final_input = self._get_input_from_user(feature_values)

        return Dataset(final_input, target=None)

    def __call__(self, features_dict: dict) -> str:
        """Execute the Tool's functionality.

        Predict an outcome based on rows from the dataset or on input formed from the user query.

        Parameters
        ----------
        features_dict : dict
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        str
            The model's prediction.
        """
        model_input = self._prepare_input(features_dict)
        prediction = self._model.predict(model_input).prediction
        return ", ".join(map(str, prediction))
