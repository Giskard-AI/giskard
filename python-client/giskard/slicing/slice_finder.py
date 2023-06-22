from typing import Optional, Sequence


from .text_slicer import TextSlicer

from .category_slicer import CategorySlicer

from .utils import get_slicer
from ..datasets.base import Dataset


class SliceFinder:
    def __init__(self, numerical_slicer="tree"):
        self.numerical_slicer = numerical_slicer

    def run(self, dataset: Dataset, features: Sequence[str], target: Optional[str] = None):
        target = target or dataset.target

        if target is None:
            raise ValueError("Target must be specified.")

        # Columns by type
        cols_by_type = {
            type_val: [
                col for col, col_type in dataset.column_types.items() if col_type == type_val and col in features
            ]
            for type_val in ["numeric", "category", "text"]
        }

        sliced_features = {}

        # Numerical features
        slicer = get_slicer(self.numerical_slicer, dataset, target)
        for col in cols_by_type["numeric"]:
            sliced_features[col] = slicer.find_slices([col])

        # Categorical features
        slicer = CategorySlicer(dataset, target=target)
        for col in cols_by_type["category"]:
            sliced_features[col] = slicer.find_slices([col])

        # Text features (currently, only if target is numeric)
        slicer = TextSlicer(dataset, target=target, slicer=self.numerical_slicer)
        for col in cols_by_type["text"]:
            sliced_features[col] = slicer.find_slices([col])

        return sliced_features
