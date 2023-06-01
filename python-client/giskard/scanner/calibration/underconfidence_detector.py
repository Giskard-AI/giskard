from typing import Sequence
import numpy as np
import pandas as pd

from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...models.base import BaseModel
from ...datasets import Dataset
from ..decorators import detector
from ..common.loss_based_detector import LossBasedDetector
from .issues import CalibrationIssue, CalibrationIssueInfo, UnderconfidenceIssue
from ..logger import logger


@detector(name="underconfidence", tags=["underconfidence", "classification"])
class UnderconfidenceDetector(LossBasedDetector):
    def __init__(self, threshold=0.10, method="tree"):
        self.threshold = threshold
        self.method = method

    @property
    def _numerical_slicer_method(self):
        return self.method

    def run(self, model: BaseModel, dataset: Dataset):
        if not model.is_classification:
            raise ValueError("Underconfidence detector only works for classification models.")

        return super().run(model, dataset)

    def _calculate_loss(self, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
        # Empirical cost associated to underconfidence: difference between
        # the two most probable classes.
        ps = model.predict(dataset).raw
        loss_values = -np.abs(np.diff(np.partition(-ps, 1, axis=-1)[:, :2], axis=-1).squeeze(-1))

        return pd.DataFrame({self.LOSS_COLUMN_NAME: loss_values}, index=dataset.df.index)

    def _find_issues(
        self,
        slices: Sequence[SlicingFunction],
        model: BaseModel,
        dataset: Dataset,
        meta: pd.DataFrame,
    ) -> Sequence[CalibrationIssue]:
        # Add the loss column to the dataset
        dataset_with_meta = Dataset(
            dataset.df.join(meta, how="left"),
            target=dataset.target,
            column_types=dataset.column_types,
        )
        mean_loss = dataset_with_meta.df[self.LOSS_COLUMN_NAME].mean()

        issues = []
        for slice_fn in slices:
            sliced_dataset = dataset_with_meta.slice(slice_fn)

            slice_loss = sliced_dataset.df[self.LOSS_COLUMN_NAME].mean()
            relative_delta = (slice_loss - mean_loss) / mean_loss

            logger.debug(
                f"{self.__class__.__name__}: Testing slice {slice_fn}\tLoss (slice) = {slice_loss:.3f} (global {mean_loss:.3f}) Δm = {relative_delta:.3f}"
            )

            if relative_delta > self.threshold:
                level = "major" if relative_delta > 2 * self.threshold else "medium"
                issues.append(
                    UnderconfidenceIssue(
                        model,
                        dataset,
                        level,
                        CalibrationIssueInfo(
                            slice_fn=slice_fn,
                            slice_size=len(sliced_dataset),
                            metric_value_slice=slice_loss,
                            metric_value_reference=mean_loss,
                            loss_values=meta[self.LOSS_COLUMN_NAME],
                            threshold=self.threshold,
                        ),
                    )
                )

        return issues
