from typing import Sequence
import numpy as np
import pandas as pd

from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...models.base import BaseModel
from ...datasets import Dataset
from ..decorators import detector
from ..common.loss_based_detector import LossBasedDetector
from .issues import CalibrationIssue, CalibrationIssueInfo


@detector(name="overconfidence", tags=["overconfidence", "classification"])
class OverconfidenceBiasDetector(LossBasedDetector):
    def __init__(self, threshold=0.10, method="tree"):
        self.threshold = threshold
        self.method = method

    @property
    def _numerical_slicer_method(self):
        return self.method

    def run(self, model: BaseModel, dataset: Dataset):
        if not model.is_classification:
            raise ValueError("Overconfidence bias detector only works for classification models.")

        return super().run(model, dataset)

    def _calculate_loss(self, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
        true_target = dataset.df.loc[:, dataset.target].values
        pred = model.predict(dataset)
        label2id = {label: n for n, label in enumerate(model.meta.classification_labels)}

        # Empirical cost associated to overconfidence
        p_max = pred.probabilities
        p_true_label = np.array([pred.raw[n, label2id[label]] for n, label in enumerate(true_target)])

        loss_values = p_max - p_true_label
        mask = loss_values > 0

        return pd.DataFrame({self.LOSS_COLUMN_NAME: loss_values[mask]}, index=dataset.df.index[mask])

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

            if relative_delta > self.threshold:
                level = "major" if relative_delta > 2 * self.threshold else "medium"
                issues.append(
                    CalibrationIssue(
                        model,
                        dataset,
                        level,
                        CalibrationIssueInfo(
                            slice_fn=slice_fn,
                            slice_size=len(sliced_dataset),
                            metric_value_slice=slice_loss,
                            metric_value_reference=mean_loss,
                            threshold=self.threshold,
                        ),
                    )
                )

        return issues
