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
            test_name=None
    ):
        self.slice_fn = slice_fn
        self.model = model
        self.dataset = dataset
        self.test_results = test_results
        self.test_name = test_name

    def __repr__(self):
        return f"<Issue {(self.slice_fn.query.get_all_clauses()[0].to_pandas(), self.test_results.passed, self.test_results.metric,self.test_name)}>"
