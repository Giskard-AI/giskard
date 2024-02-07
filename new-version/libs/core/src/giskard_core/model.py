from typing import Any

from abc import ABC, abstractmethod

from giskard_core.dataset import Dataset


class Model(ABC):

    @abstractmethod
    def __call__(self, dataset: Dataset) -> Any:
        raise NotImplementedError
