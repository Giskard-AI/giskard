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
    name = "predict_from_dataset"

    def __init__(self, model: BaseModel, dataset: Dataset):
        self._model = model
        self._dataset = dataset

    def _get_feature_json_type(self):
        number_columns = {column: "number" for column in self._dataset.df.select_dtypes(include=(int, float)).columns}
        string_columns = {column: "string" for column in self._dataset.df.select_dtypes(exclude=(int, float)).columns}
        return number_columns | string_columns

    @property
    def specification(self) -> str:
        feature_json_type = self._get_feature_json_type()

        return {
            "name": PredictFromDatasetTool.name,
            "description": "Using given filter, extract rows from the dataset and run model prediction on them",
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
