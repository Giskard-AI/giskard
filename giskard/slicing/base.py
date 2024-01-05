from typing import List, Optional, Sequence

from abc import ABC, abstractmethod

from ..datasets.base import Dataset
from .slice import QueryBasedSliceFunction


class BaseSlicer(ABC):
    def __init__(
        self,
        dataset: Dataset,
        features: Optional[Sequence[str]] = None,
        target: Optional[str] = None,
        min_deviation: float = 0.05,
        abs_deviation: bool = False,
    ):
        self.dataset = dataset
        self.features = features
        self.target = target
        self.min_deviation = min_deviation
        self.abs_deviation = abs_deviation

    @abstractmethod
    def find_slices(self, features, target=None) -> List[QueryBasedSliceFunction]:
        ...
