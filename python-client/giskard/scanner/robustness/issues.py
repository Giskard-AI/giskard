import numpy as np
import pandas as pd
from dataclasses import dataclass
from functools import lru_cache
from typing import List

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
    def features(self) -> List[str]:
        return [self.info.feature]

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

    @lru_cache
    def examples(self, n=3) -> pd.DataFrame:
        rng = np.random.default_rng(142)
        idx = rng.choice(self.info.fail_data_idx, min(len(self.info.fail_data_idx), n), replace=False)

        data = self.dataset.slice(lambda df: df.loc[idx], row_level=False)
        perturbed_data = self.info.perturbed_data_slice.slice(lambda df: df.loc[idx], row_level=False)

        examples = self.dataset.df.loc[idx, (self.info.feature,)].copy()

        original_preds = pd.Series(self.model.predict(data).prediction, index=idx)
        perturbed_preds = pd.Series(self.model.predict(perturbed_data).prediction, index=idx)

        # Add transformed feature
        examples[f"{self.info.transformation_fn.name}({self.info.feature})"] = perturbed_data.df.loc[
            idx, self.info.feature
        ]

        # Add predictions
        examples["Original prediction"] = original_preds.loc[examples.index]
        examples["Prediction after perturbation"] = perturbed_preds.loc[examples.index]

        return examples

    @property
    def importance(self) -> float:
        return self.info.fail_ratio

    @property
    def transformation_fn(self):
        return self.info.transformation_fn

    def generate_tests(self, with_names=False) -> list:
        from ...testing.tests.metamorphic import test_metamorphic_invariance

        tests = [
            test_metamorphic_invariance(
                model=self.model,
                dataset=self.dataset,
                transformation_function=self.info.transformation_fn,
                slicing_function=None,
                threshold=1 - self.info.threshold,
                output_sensitivity=self.info.output_sensitivity,
            )
        ]

        if with_names:
            names = [f"Invariance to “{self.info.transformation_fn.name}”"]
            return list(zip(tests, names))

        return tests


class EthicalIssue(RobustnessIssue):
    group = "Ethics"
