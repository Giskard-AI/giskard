from typing import Optional, Sequence

import datetime
from abc import abstractmethod
from time import perf_counter

import pandas as pd

from giskard.scanner.common.utils import get_dataset_subsample
from giskard.utils.xprint import BOLD_STYLE, CYAN_STYLE, GREEN_STYLE, RED_STYLE, Template

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ...registry.slicing_function import SlicingFunction
from ...slicing.slice_finder import SliceFinder
from ..issues import Issue
from ..registry import Detector
from ..scanlogger import logger

NotEnoughData = Template(content="Skipping scan because the dataset is too small (< {} samples).", pstyles=[RED_STYLE])
LimitSize = Template(content="Limiting dataset size to {} samples.", pstyles=[CYAN_STYLE])
LossDone = Template(content="Loss calculated (took {})", pstyles=[BOLD_STYLE])
NumberSlicesFound = Template(content="{} slices found (took {})", pstyles=[BOLD_STYLE, BOLD_STYLE])
IssuesNumber = Template(content="{} issues found (took {})", pstyles=[RED_STYLE, BOLD_STYLE])
NoIssues = Template(content="{} issues found (took {})", pstyles=[GREEN_STYLE, BOLD_STYLE])
Red = Template(content="{}", pstyles=[RED_STYLE])


class LossBasedDetector(Detector):
    MIN_DATASET_LENGTH = 100
    MAX_DATASET_SIZE = 10_000_000
    LOSS_COLUMN_NAME = "__gsk__loss"

    _needs_target = True

    def __init__(self, max_dataset_size: Optional[int] = None):
        self.max_dataset_size = max_dataset_size

    def run(self, model: BaseModel, dataset: Dataset, features: Sequence[str]):
        if self._needs_target and dataset.target is None:
            logger.critical("Skipping detection because the dataset has no target column.", template=Red)
            return []

        # Check if we have enough data to run the scan
        if len(dataset) < self.MIN_DATASET_LENGTH:
            logger.critical(self.MIN_DATASET_LENGTH, template=NotEnoughData)
            return []

        # If the dataset is very large, limit to a subsample
        self.max_dataset_size = self.max_dataset_size or self.MAX_DATASET_SIZE // len(features)
        if len(dataset) > self.max_dataset_size:
            logger.info(self.max_dataset_size, template=LimitSize)
            dataset = get_dataset_subsample(dataset, model, self.max_dataset_size)

        # Calculate loss
        logger.info("Computing loss")
        start = perf_counter()
        meta = self._calculate_loss(model, dataset)
        elapsed = perf_counter() - start
        logger.info(datetime.timedelta(seconds=elapsed), template=LossDone)

        # Find slices
        logger.info("Finding data slices")
        start = perf_counter()
        slices = self._find_slices(model, dataset, features, meta)
        elapsed = perf_counter() - start
        logger.info(len(slices), datetime.timedelta(seconds=elapsed), template=NumberSlicesFound)

        # Create issues from the slices
        logger.info("Analyzing issues")
        issues = self._find_issues(slices, model, dataset, meta)
        return issues

    @property
    def _numerical_slicer_method(self):
        return "tree"

    def _find_slices(self, model: BaseModel, dataset: Dataset, features: Sequence[str], meta: pd.DataFrame):
        df_with_meta = dataset.df.join(meta, how="right")

        column_types = dataset.column_types.copy()
        column_types[self.LOSS_COLUMN_NAME] = "numeric"
        dataset_with_meta = Dataset(
            df_with_meta,
            target=dataset.target,
            column_types=column_types,
            validation=False,
        )

        # For performance
        dataset_with_meta.load_metadata_from_instance(dataset.column_meta)

        # Find slices
        sf = SliceFinder(numerical_slicer=self._numerical_slicer_method)
        sliced = sf.run(dataset_with_meta, features, target=self.LOSS_COLUMN_NAME)
        slices = sum(sliced.values(), start=[])

        # Keep only slices of size at least 5% of the dataset or 20 samples (whatever is larger) and conversely exclude
        # slices which are larger than 95% of the dataset
        slices = [
            s for s in slices if max(0.05 * len(dataset), 20) <= len(dataset_with_meta.slice(s)) <= 0.95 * len(dataset)
        ]

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
