from typing import Optional, Sequence

from ..datasets.base import Dataset
from .category_slicer import CategorySlicer
from .text_slicer import TextSlicer
from .utils import get_slicer


class SliceFinder:
    def __init__(self, numerical_slicer="tree"):
        self.numerical_slicer = numerical_slicer

    def run(
        self,
        dataset: Dataset,
        features: Sequence[str],
        target: Optional[str] = None,
        min_slice_size: Optional[float] = None,
    ):
        if min_slice_size and len(dataset) < min_slice_size:
            return dict()

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
            sliced_features[col] = slicer.find_slices([col], min_samples=min_slice_size)

        # Categorical features
        slicer = CategorySlicer(dataset, target=target)
        for col in cols_by_type["category"]:
            sliced_features[col] = slicer.find_slices([col])

        # Text features (currently, only if target is numeric)
        slicer = TextSlicer(dataset, target=target, slicer=self.numerical_slicer)
        for col in cols_by_type["text"]:
            sliced_features[col] = slicer.find_slices([col], min_samples=min_slice_size)

        return sliced_features
