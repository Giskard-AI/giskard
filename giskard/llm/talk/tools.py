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

    def __call__(self, *args, **kwargs):
        raise NotImplementedError
