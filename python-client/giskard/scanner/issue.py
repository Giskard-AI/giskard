from ..datasets import Dataset
from ..models.base import BaseModel
from ..ml_worker.testing.registry.slice_function import SliceFunction

from typing import Optional, Callable


class Issue:
    def __init__(
        self,
        slice_fn: SliceFunction,
        model: Optional[BaseModel] = None,
        dataset: Optional[Dataset] = None,
        test_results=None,
    ):
        self.slice_fn = slice_fn
        self.model = model
        self.dataset = dataset
        self.test_results = test_results
    