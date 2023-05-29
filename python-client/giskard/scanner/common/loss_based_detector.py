import pandas as pd
from typing import Sequence
from abc import abstractmethod

from ...models.base import BaseModel
from ...datasets.base import Dataset
from ...slicing.utils import get_slicer
from ...slicing.text_slicer import TextSlicer
from ...slicing.category_slicer import CategorySlicer
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ..logger import logger
from ..issues import Issue


class LossBasedDetector:
    MIN_DATASET_LENGTH = 100
    MAX_DATASET_SIZE = 10_000_000
    LOSS_COLUMN_NAME = "__gsk__loss"

    def run(self, model: BaseModel, dataset: Dataset):
        logger.debug(f"{self.__class__.__name__}: Running")

        # Check if we have enough data to run the scan
        if len(dataset) < self.MIN_DATASET_LENGTH:
            logger.warning(
                f"{self.__class__.__name__}: Skipping scan because the dataset is too small"
                " (< {self.MIN_DATASET_LENGTH} samples)."
            )
            return []

        # If the dataset is very large, limit to a subsample
        max_data_size = self.MAX_DATASET_SIZE // len(model.meta.feature_names or dataset.columns)
        if len(dataset) > max_data_size:
            logger.debug(f"{self.__class__.__name__}: Limiting dataset size to {max_data_size} samples.")
            dataset = dataset.slice(lambda df: df.sample(max_data_size, random_state=42), row_level=False)

        # Calculate loss
        meta = self._calculate_loss(model, dataset)

        # Find slices
        dataset_to_slice = dataset.select_columns(model.meta.feature_names) if model.meta.feature_names else dataset
        slices = self._find_slices(dataset_to_slice, meta)

        # Create issues from the slices
        issues = self._find_issues(slices, model, dataset, meta)

        return issues

    @property
    def _numerical_slicer_method(self):
        return "tree"

    def _find_slices(self, dataset: Dataset, meta: pd.DataFrame):
        df_with_meta = dataset.df.join(meta, how="right")

        column_types = dataset.column_types.copy()
        column_types[self.LOSS_COLUMN_NAME] = "numeric"
        dataset_with_meta = Dataset(df_with_meta, target=dataset.target, column_types=column_types)

        # Columns by type
        cols_by_type = {
            type_val: [col for col, col_type in dataset.column_types.items() if col_type == type_val]
            for type_val in ["numeric", "category", "text"]
        }

        # Numerical features
        slicer = get_slicer(self._numerical_slicer_method, dataset_with_meta, self.LOSS_COLUMN_NAME)

        slices = []
        for col in cols_by_type["numeric"]:
            slices.extend(slicer.find_slices([col]))

        # Categorical features
        slicer = CategorySlicer(dataset_with_meta, target=self.LOSS_COLUMN_NAME)
        for col in cols_by_type["category"]:
            slices.extend(slicer.find_slices([col]))

        # Text features
        slicer = TextSlicer(dataset_with_meta, target=self.LOSS_COLUMN_NAME, slicer=self._numerical_slicer_method)
        for col in cols_by_type["text"]:
            slices.extend(slicer.find_slices([col]))

        # Keep only slices of size at least 5% of the dataset or 20 samples (whatever is larger)
        slices = [s for s in slices if max(0.05 * len(dataset), 20) <= len(dataset_with_meta.slice(s))]

        return slices

    @abstractmethod
    def _calculate_loss(self, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
        ...

    @abstractmethod
    def _find_issues(
        self,
        slices: Sequence[SlicingFunction],
        model: BaseModel,
        dataset: Dataset,
        meta: pd.DataFrame,
    ) -> Sequence[Issue]:
        ...
