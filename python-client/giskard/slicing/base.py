import pandas as pd
from typing import Sequence, List

from ..datasets.base import Dataset
from .slice import QueryBasedSliceFunction


class BaseSlicer:
    def __init__(
        self,
        dataset: Dataset,
        features: Sequence[str] | None = None,
        target: str | None = None,
        min_deviation: float = 0.1,
        abs_deviation: bool = False,
    ):
        self.dataset = dataset
        self.features = features
        self.target = target
        self.min_deviation = min_deviation
        self.abs_deviation = abs_deviation

    def find_slices(self) -> List[QueryBasedSliceFunction]:
        raise NotImplementedError()
