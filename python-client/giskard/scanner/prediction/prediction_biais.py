from collections import defaultdict
import pandas as pd
from typing import Optional, Sequence
from ...models.base import BaseModel
from ...models._precooked import PrecookedModel
from ...datasets.base import Dataset
from ...slicing.utils import get_slicer
from ...slicing.text_slicer import TextSlicer
from ...slicing.category_slicer import CategorySlicer
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.scanner.performance.issues import PerformanceIssue, PerformanceIssueInfo
from giskard.scanner.performance.metrics import PerformanceMetric, get_metric
from ..decorators import detector
from ..logger import logger
from giskard.scanner.prediction.metric import OverconfidenceDetector
from giskard.scanner.performance.model_bias_detector import ModelBiasDetector,IssueFinder

class PredictionBiasDetector(ModelBiasDetector):

    def run(self, model: BaseModel, dataset: Dataset):
        logger.debug(
            f"ModelBiasDetector: Running with metrics={self.metrics}, threshold={self.threshold}, method={self.method}"
        )

        # Check if we have enough data to run the scan
        if len(dataset) < 100:
            logger.warning("ModelBiasDetector: Skipping scan because the dataset is too small.")
            return []

        # If the dataset is very large, limit to a subsample
        max_data_size = 10_000_000 // len(model.meta.feature_names)
        if len(dataset) > max_data_size:
            logger.debug(f"ModelBiasDetector: Limiting dataset size to {max_data_size} samples.")
            dataset = dataset.slice(lambda df: df.sample(max_data_size, random_state=42), row_level=False)

        oc = OverconfidenceDetector(model, dataset)
        meta = oc.get_dataset()

        # Find slices
        slices = self._find_slices(meta.select_columns(columns=dataset.df.columns), meta.df["__gsk__loss"])

        # Keep only slices of size at least 5% of the dataset
        slices = [s for s in slices if 0.05 * len(dataset) <= len(dataset.slice(s))]

        # Create issues from the slices
        issues = self._find_issues(slices, model, meta.select_columns(columns=dataset.df.columns))

        return issues


    def _find_issues(
        self,
        slices: Sequence[SlicingFunction],
        model: BaseModel,
        dataset: Dataset,
    ) -> Sequence[PerformanceIssue]:
        # Use a precooked model to speed up the tests
        precooked = PrecookedModel.from_model(model, dataset)
        detector = OverconfidenceIssueFinder(self.metrics, self.threshold)
        issues = detector.detect(precooked, dataset, slices)

        # Restore the original model
        for issue in issues:
            issue.model = model

        return issues


class OverconfidenceIssueFinder(IssueFinder):

    def detect(self, model: BaseModel, dataset: Dataset, slices: Sequence[SlicingFunction]):
        logger.debug(f"ModelBiasDetector: Testing {len(slices)} slices for performance issues.")

        # Prepare metrics
        metrics = [self._proba_rmse]

        issues = []

        for metric in metrics:
            issues.extend(self._detect_for_metric(model, dataset, slices, metric))

        # Group issues by slice and keep only the most critical
        issues_by_slice = defaultdict(list)
        for issue in issues:
            issues_by_slice[issue.info.slice_fn].append(issue)

        return sorted(
            [max(group, key=lambda i: i.importance) for group in issues_by_slice.values()], key=lambda i: i.importance
        )

    def _proba_rmse(self,model,dataset):
        return OverconfidenceDetector(model, dataset).get_proba_rmse()

    _proba_rmse.name = "proba_rmse"
    _proba_rmse.greater_is_better=False
