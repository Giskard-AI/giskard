import pandas as pd
from typing import Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..datasets import Dataset
from ..models.base import BaseModel


@dataclass
class IssueInfo(ABC):
    """Abstract class for issue information."""


class Issue:
    group: str = "Other"

    def __init__(
        self,
        model: BaseModel,
        dataset: Dataset,
        level: str,
        info: Optional[IssueInfo] = None,
    ):
        self.model = model
        self.dataset = dataset
        self.level = level.lower()
        self.info = info

    def __repr__(self):
        return f"<Issue level='{self.level}'>"

    @property
    def is_major(self) -> bool:
        return self.level == "major"

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

    def generate_tests(self) -> list:
        return []
