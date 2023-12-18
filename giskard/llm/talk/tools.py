from abc import ABC, abstractmethod

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
    def __init__(self, model: BaseModel, dataset: Dataset):
        self._model = model
        self._dataset = dataset

    @property
    def specification(self) -> str:
        raise NotImplementedError

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
