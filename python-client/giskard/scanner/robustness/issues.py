from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..issues import Issue
from ...datasets.base import Dataset
from ...ml_worker.testing.registry.transformation_function import TransformationFunction
from ...models.base import BaseModel, ModelPredictionResults


@dataclass
class RobustnessIssueInfo:
    feature: str
    transformation_fn: TransformationFunction
    fail_ratio: float
    perturbed_data_slice: Dataset
    perturbed_data_slice_predictions: ModelPredictionResults
    fail_data_idx: list
    threshold: float
    output_sensitivity: float


class RobustnessIssue(Issue):
    group = "Robustness"
    info: RobustnessIssueInfo

    def __init__(self, model: BaseModel, dataset: Dataset, level: str, info: RobustnessIssueInfo):
        super().__init__(model, dataset, level, info)

    @property
    def is_major(self) -> bool:
        return self.level == "major"

    @property
    def domain(self) -> str:
        return f"Feature `{self.info.feature}`"

    @property
    def metric(self) -> str:
        return self.info.transformation_fn.name

    @property
    def deviation(self) -> str:
        return f"{self.info.fail_ratio * 100:.2f}% of samples changed prediction after perturbation"

    @property
    def description(self) -> str:
        return ""

    def examples(self, n=3) -> pd.DataFrame:
        idx = np.random.choice(self.info.fail_data_idx, min(len(self.info.fail_data_idx), n))

        return self.dataset.df.loc[idx]

    @property
    def importance(self) -> float:
        return self.info.fail_ratio

    def generate_tests(self) -> list:
        from ...ml_worker.testing.tests.metamorphic import test_metamorphic_invariance

        return [
            test_metamorphic_invariance(
                self.model,
                self.dataset,
                self.info.transformation_fn,
                threshold=1 - self.info.threshold,
                output_sensitivity=self.info.output_sensitivity,
            )
        ]
