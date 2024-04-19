from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from abc import ABC, abstractmethod
from difflib import SequenceMatcher as SeqM

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from giskard.llm.talk.config import FUZZY_SIMILARITY_THRESHOLD

if TYPE_CHECKING:
    from giskard.datasets.base import Dataset
    from giskard.models.base import BaseModel


class BaseTool(ABC):
    """Base class of the Tool object.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

    default_name: str = ...
    default_description: str = ...

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Constructor of the class.

        Parameters
        ----------
        name : str, optional
            The name of the Tool. If not set, the `default_name` is used.
        description : str, optional
            The description of the Tool. If not set, the `default_description` is used.
        """
        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        """Return the name of the Tool.

        Returns
        -------
        str
            The name of the Tool.
        """
        return self._name

    @property
    def description(self) -> str:
        """Return the description of the Tool.

        Returns
        -------
        str
            The description of the Tool.
        """
        return self._description

    @property
    @abstractmethod
    def specification(self) -> str:
        """Return the Tool's specification in a JSON Schema format.

        Returns
        -------
        str
            The Tool's specification.
        """
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        """Execute the Tool's functionality.

        Returns
        -------
        str
            The result of the Tool's execution.
        """
        ...


class PredictionMixin(ABC):
    """A mix-in class to introduce methods for a prediction."""

    def __init__(self, model: BaseModel, dataset: Dataset):
        """Constructor of the class.

        Parameters
        ----------
        model : BaseModel
            The Giskard Model.
        dataset : Dataset
            The Giskard Dataset.
        """
        self._model = model
        self._dataset = dataset

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

    @property
    def features_json_type(self) -> dict[str, str]:
        """Get features' JSON type.

        Determine the JSON type of features from the tool's `dataset`.

        Returns
        -------
        dict[str, str]
            The dictionary with feature names and related JSON types.
        """
        features_json_type = dict()

        for col in self._dataset.df:
            if is_bool_dtype(self._dataset.df[col]):
                features_json_type[col] = "boolean"
            elif is_numeric_dtype(self._dataset.df[col]):
                features_json_type[col] = "number"
            else:
                # String, datetime and category.
                features_json_type[col] = "string"

        return features_json_type
