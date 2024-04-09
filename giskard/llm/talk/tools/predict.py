from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pandas as pd

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.base import BaseTool, PredictionMixin

if TYPE_CHECKING:
    from giskard.models.base import BaseModel


class PredictTool(BaseTool, PredictionMixin):
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
