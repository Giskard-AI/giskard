import pandas as pd
from typing import List, Optional, Any
from abc import ABC, abstractmethod

from ..datasets import Dataset
from ..models.base import BaseModel


class Issue(ABC):
    group: str = "Other"

    def __init__(
        self,
        model: BaseModel,
        dataset: Dataset,
        level: str,
        info: Optional[Any] = None,
    ):
        self.model = model
        self.dataset = dataset
        self.level = level.lower()
        self.info = info

    def __repr__(self):
        return f"<{self.__class__.__name__} level='{self.level}'>"

    @property
    def is_major(self) -> bool:
        return self.level == "major"

    @property
    def features(self) -> List[str]:
        return []

    @property
    @abstractmethod
    def domain(self) -> str:
        ...

    @property
    @abstractmethod
    def metric(self) -> str:
        ...

    @property
    @abstractmethod
    def deviation(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def examples(self, n=3) -> pd.DataFrame:
        ...

    @property
    @abstractmethod
    def importance(self) -> float:
        ...

    @property
    def slicing_fn(self):
        return None

    @property
    def transformation_fn(self):
        return None

    def generate_tests(self, with_names=False) -> list:
        return []
