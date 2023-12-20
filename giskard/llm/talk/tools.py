from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from giskard.models.base import BaseModel

from giskard.datasets.base import Dataset


class BaseTool(ABC):
    @property
    @abstractmethod
    def specification(self) -> str:
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        ...


class PredictFromDatasetTool(BaseTool):
    default_name = "predict_from_dataset"
    default_description = ("From the user input, it extracts a necessary information to filter rows from the dataset, "
                           "then it runs the model prediction on that rows and finally returns the prediction result.")

    def __init__(self, model: BaseModel, dataset: Dataset, name: str = None, description: str = None):
        self._model = model
        self._dataset = dataset

        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def _get_feature_json_type(self):
        number_columns = {column: "number" for column in self._dataset.df.select_dtypes(include=(int, float)).columns}
        string_columns = {column: "string" for column in self._dataset.df.select_dtypes(exclude=(int, float)).columns}
        return number_columns | string_columns

    @property
    def specification(self) -> str:
        feature_json_type = self._get_feature_json_type()

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "row_filter": {
                        "type": "object",
                        "properties": {feature: {"type": dtype} for feature, dtype in feature_json_type.items()}
                    }
                },
                "required": ["row_filter"]
            }
        }

    def _get_filtered_dataset(self, row_filter: dict) -> Dataset:
        filtered_df = self._dataset.df.copy()
        for col_name, col_value in row_filter.items():
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[filtered_df[col_name].str.lower() == str(col_value).lower()]
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df)

    def __call__(self, row_filter: dict) -> str:
        # 1) Filter dataset using predicted filter.
        filtered_dataset = self._get_filtered_dataset(row_filter)

        # 2) Get model prediction.
        prediction = self._model.predict(filtered_dataset).prediction

        # 3) Finalise the result.
        result = ", ".join(prediction)

        return result
