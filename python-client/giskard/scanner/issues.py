from ..datasets import Dataset
from ..models.base import BaseModel

from typing import Optional


class IssueInfo:
    pass


class Issue:
    group: str = "Other"

    domain: str
    metric: str
    deviation: str
    description: str

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
    def is_major(self):
        return self.level == "major"
