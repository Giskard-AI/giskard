from dataclasses import dataclass

from ..issues import Issue, IssueInfo
from ...models.base import BaseModel
from ...datasets.base import Dataset


@dataclass
class RobustnessIssueInfo(IssueInfo):
    actual_slices_size: int
    metric: float
    passed: bool
    messages: str


class RobustnessIssue(Issue):
    """Performance Issue"""

    def __init__(
            self,
            model: BaseModel,
            dataset: Dataset,
            level: str,
            info: RobustnessIssueInfo,
    ):
        super().__init__(model, dataset, level, info)
