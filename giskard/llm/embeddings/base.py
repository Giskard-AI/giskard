from typing import Sequence

from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedding(ABC):
    @abstractmethod
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        ...
