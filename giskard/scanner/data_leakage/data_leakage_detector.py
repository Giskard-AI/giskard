from typing import Optional, Sequence

import numpy as np
import pandas as pd

from giskard.datasets import Dataset
from giskard.models import cache as models_cache
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import DataLeakage, Issue, IssueLevel
from giskard.scanner.logger import logger

from ..registry import Detector


@detector(name="data_leakage", tags=["data_leakage", "classification", "regression"])
class DataLeakageDetector(Detector):
    def run(self, model: BaseModel, dataset: Dataset, features: Optional[Sequence[str]] = None):
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
            return [
                Issue(
                    model,
                    dataset,
                    group=DataLeakage,
                    level=IssueLevel.MAJOR,
                    description=f"We found {len(fail_samples)} examples for which the model provides a different output depending on whether it is computing on a single data point or on a batch.",
                    examples=fail_samples,
                    meta={"domain": "Whole dataset"},
                    taxonomy=["avid-effect:performance:P0103"],
                    detector_name=self.__class__.__name__,
                )
            ]

        return []
