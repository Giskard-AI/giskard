from abc import ABC, abstractmethod
from typing import Sequence, List, Optional

from .slice import QueryBasedSliceFunction
from ..datasets.base import Dataset


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
