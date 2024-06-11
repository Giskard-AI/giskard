from typing import Dict, Optional, Sequence

from abc import ABC, abstractmethod
from collections import defaultdict

from ..datasets.base import Dataset
from ..models.base import BaseModel
from .issues import Issue


class Detector(ABC):
    @abstractmethod
    def run(self, model: BaseModel, dataset: Dataset, features: Sequence[str]) -> Sequence[Issue]:
        ...


class DetectorRegistry:
    _detectors: Dict[str, Detector] = dict()
    _tags = defaultdict(set)

    @classmethod
    def register(cls, name: str, detector: Detector, tags: Optional[Sequence[str]] = None):
        cls._detectors[name] = detector
        if tags is not None:
            cls._tags[name] = set(tags)

    @classmethod
    def get_detector_classes(cls, tags: Optional[Sequence[str]] = None) -> dict:
        if tags is None:
            return {n: d for n, d in cls._detectors.items()}

        return {n: d for n, d in cls._detectors.items() if cls._tags[n].intersection(tags)}
