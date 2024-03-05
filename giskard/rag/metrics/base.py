from typing import Sequence

from abc import ABC, abstractmethod

from ..testset import QATestset


class Metric(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def __call__(self, testset: QATestset, answers: Sequence[str], *args, **kwargs):
        ...
