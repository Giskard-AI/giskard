from typing import Sequence
from giskard.datasets import Dataset
from giskard.models.base import BaseModel, ModelPredictionResults
from ...slicing.text_slicer import TextSlicer
from ...slicing.tree_slicer import DecisionTreeSlicer
from ...slicing.category_slicer import CategorySlicer

from ..issues import Issue
from ..decorators import detector
from ..logger import logger


@detector(name="spurious_correlation", tags=["spurious_correlation", "classification"])
class SpuriousCorrelationDetector:
    def __init__(self, alpha=1e-3):
        self.alpha = alpha

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        logger.debug(f"SpuriousCorrelationDetector: Running with alpha={self.alpha}")

        if not model.is_classification:
            logger.warning(
                "SpuriousCorrelationDetector: Skipping scan because the model is not a classification model."
            )
            return []

        model_pred = model.predict(dataset)
        dataset_to_slice = dataset.select_columns(model.meta.feature_names) if model.meta.feature_names else dataset
        issues = self._find_issues(dataset_to_slice, model_pred)


        return issues

    def _find_issues(self, dataset: Dataset, model_pred: ModelPredictionResults):
        dataset_with_meta = dataset.copy()
        dataset_with_meta.df["__gsk__prediction"] = model_pred.prediction

        cols_by_type = {
            type_val: [col for col, col_type in dataset.column_types.items() if col_type == type_val]
            for type_val in ["numeric", "category", "text"]
        }

        issues = []

        # Categorycal features
        for col in cols_by_type["category"]:
            # We directly perform a χ² test with the contingency table
            values = dataset.df[col].dropna()

        # Numerical features
        slicer = DecisionTreeSlicer(dataset, target="__gsk__prediction")
        for col in cols_by_type["numeric"]:
            slices.extend(slicer.find_slices(col))

        # Text features
        slicer = TextSlicer(dataset, target=model_pred.prediction)
        for col in cols_by_type["text"]:
            slices.extend(slicer.find_slices(col))

        return issues
    
