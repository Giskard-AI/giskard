from difflib import SequenceMatcher as SeqM

import pandas as pd

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import FUZZY_SIMILARITY_THRESHOLD, ToolDescription
from giskard.llm.talk.tools.base import BaseTool


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
        -------x
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
                        "features_dict": {
                            "type": "object",
                            "properties": {
                                feature: {"type": dtype} for feature, dtype in self.features_json_type.items()
                            },
                        }
                    },
                    "required": ["features_dict"],
                },
            },
        }

    def _get_input_from_dataset(self, row_filter: dict[str, any]) -> pd.DataFrame:
        """Get input from dataset.

        Filter rows from the dataset, using the `row_filter`.

        Parameters
        ----------
        row_filter : dict[str, any]
            The dictionary with features and related values to filter the dataset.

        Returns
        -------
        pd.DataFrame
            The DataFrame with filtered rows.
        """
        filtered_df = self._dataset.df
        for col_name, col_value in row_filter.items():
            # Use fuzzy comparison to filter string features.
            if self.features_json_type[col_name] == "string":
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

        return filtered_df

    def _get_input_from_user(self, feature_values: dict[str, any]) -> pd.DataFrame:
        """Form input based on the user's query.

        Take input feature values from user query. For the missed values, take the feature mean from the Dataset.

        Parameters
        ----------
        feature_values : dict[str, any]
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        pd.DataFrame
            The DataFrame with the formed input.
        """
        # Import the private function from the 'model_explanation' module to avoid code duplication.
        # Also, if import from the top-level, we get the next error: "ImportError: cannot import name 'BaseModel'
        # from partially initialized module 'giskard.models.base' (most likely due to a circular import)"
        from giskard.models.model_explanation import _get_background_example

        # Prepare the background sample (the median and the mode of dataset's features).
        background_df = self._model.prepare_dataframe(
            self._dataset.df, self._dataset.column_dtypes, self._dataset.target
        )
        background_sample = _get_background_example(background_df, self._dataset.column_types)

        # Fill the background sample with known values (provided by the user query).
        for col_name, col_value in feature_values.items():
            background_sample[col_name] = col_value

        return background_sample

    def _prepare_input(self, feature_values: dict[str, any]) -> Dataset:
        """Prepare model input.

        Either extract rows form the dataset, or create input from the user's query.

        Parameters
        ----------
        feature_values : dict[str, any]
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        Dataset
            The Giskard Dataset with model input.
        """
        final_input = self._get_input_from_dataset(feature_values)

        # If no data were selected from the dataset, build vector from the user input.
        if len(final_input) == 0:
            final_input = self._get_input_from_user(feature_values)

        return Dataset(final_input, target=None)

    def _validate_features_dict(self, features_dict: dict[str, any]) -> None:
        """Validate the `features_dict` contains correct features.

        Parameters
        ----------
        features_dict : dict[str, any]
            The dictionary with features and related values extracted from the query.
        """

        # Check, if 'features_dict' contains features different from the dataset.
        if not set(features_dict).issubset(self._dataset.df):
            invalid_features = set(features_dict).difference(self._dataset.df)
            raise ValueError(f"Invalid features were detected: {invalid_features}")

    def __call__(self, features_dict: dict[str, any]) -> str:
        """Execute the Tool's functionality.

        Predict an outcome based on rows from the dataset or on input formed from the user query.

        Parameters
        ----------
        features_dict : dict[str, any]
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        str
            The model's prediction.
        """
        self._validate_features_dict(features_dict)
        model_input = self._prepare_input(features_dict)
        prediction = self._model.predict(model_input).prediction
        return ", ".join(map(str, prediction))
