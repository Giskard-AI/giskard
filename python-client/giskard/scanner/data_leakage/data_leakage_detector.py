import pandas as pd
import numpy as np
from dataclasses import dataclass

from giskard import Dataset
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue
from giskard.scanner.logger import logger


@detector(name="data_leakage", tags=["data_leakage", "classification", "regression"])
class DataLeakageDetector:
    def run(self, model: BaseModel, dataset: Dataset):
        logger.debug("DataLeakageDetector: Running")

        # Dataset prediction
        ds_predictions = pd.Series(list(model.predict(dataset).raw), dataset.df.index, dtype=object)
        print(ds_predictions)
        # @TODO: disable cache
        # Predict on single samples
        sample_idx = dataset.df.sample(min(len(dataset), 100), random_state=23).index
        fail_samples = pd.DataFrame(columns=["Whole-dataset prediction", "Single-sample prediction"])
        for idx, expected_pred in zip(sample_idx, ds_predictions.loc[sample_idx]):
            row_dataset = dataset.slice(lambda df: df.loc[[idx]], row_level=False)
            row_pred = model.predict(row_dataset).raw[0]

            if not np.isclose(row_pred, expected_pred).all():
                fail_samples.loc[idx, "Whole-dataset prediction"] = expected_pred
                fail_samples.loc[idx, "Single-sample prediction"] = row_pred

            if len(fail_samples) >= 3:
                break

        if not fail_samples.empty:
            return [DataLeakageIssue(model, dataset, level="major", info=DataLeakageInfo(samples=fail_samples))]

        return []


@dataclass
class DataLeakageInfo:
    samples: pd.DataFrame


class DataLeakageIssue(Issue):
    """DataLeakage Issue"""

    group = "Data Leakage"

    @property
    def domain(self) -> str:
        return "Whole dataset"

    @property
    def metric(self) -> str:
        return "Prediction"

    @property
    def deviation(self) -> str:
        return "Model changes output when prediction is run on a single sample"

    @property
    def description(self) -> str:
        return "Your model may have some data leakage. For example, your model provides different results depending on whether it’s run on a single sample or the whole dataset."

    def examples(self, n=3) -> pd.DataFrame:
        return self.info.samples.head(n)

    @property
    def importance(self) -> float:
        return 1

    def generate_tests(self) -> list:
        return []
