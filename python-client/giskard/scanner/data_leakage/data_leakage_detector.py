import pandas as pd
import numpy as np
from dataclasses import dataclass

from giskard import Dataset
from giskard.models import cache as models_cache
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue
from giskard.scanner.logger import logger
from ..registry import Detector


@detector(name="data_leakage", tags=["data_leakage", "classification", "regression"])
class DataLeakageDetector(Detector):
    def run(self, model: BaseModel, dataset: Dataset):
        logger.info("DataLeakageDetector: Running")

        # Dataset prediction
        ds_predictions = pd.Series(list(model.predict(dataset).raw), dataset.df.index, dtype=object)

        # Predict on single samples
        sample_idx = dataset.df.sample(min(len(dataset), 100), random_state=23).index.values
        fail_samples = pd.DataFrame(columns=["Whole-dataset prediction", "Single-sample prediction"])

        def slice_single_sample(idx):
            def slice_fn(df):
                return df.loc[[idx]]

            return slice_fn

        for idx, expected_pred in zip(sample_idx, ds_predictions.loc[sample_idx].values):
            row_dataset = dataset.slice(slice_single_sample(idx), row_level=False)
            with models_cache.no_cache():
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
        return f"We found {len(self.info.samples)} examples for which the model provides a different output depending on whether it is computing on a single data point or on a batch."

    def examples(self, n=3) -> pd.DataFrame:
        return self.info.samples.head(n)

    @property
    def importance(self) -> float:
        return 1

    def generate_tests(self, with_names=False) -> list:
        return []
