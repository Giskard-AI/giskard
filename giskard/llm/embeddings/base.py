from typing import Sequence

import itertools
from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedding(ABC):
    @abstractmethod
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        ...


def batched(iterable, batch_size):
    """Batches an iterable into chunks of size batch_size."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, batch_size))
        if not chunk:
            break
        yield chunk
