import pandas as pd

from ..datasets import Dataset
from .base import BaseSlicer
from .slice import Query, LowerThan, GreaterThan, QueryBasedSliceFunction


class BruteForceSlicer(BaseSlicer):
    def __init__(self, dataset: Dataset, features=None, target=None):
        self.dataset = dataset
        self.features = features
        self.target = target

    def find_slices(self, features, target=None):
        target = target or self.target
        data = self.dataset.df

        if len(features) > 1:
            raise NotImplementedError("Only single-feature slicing is implemented for now.")
        (feature,) = features

        # Quantile-based binning
        _, cut_bin = pd.qcut(data[feature], q=10, retbins=True, duplicates="drop", labels=False)

        intervals_df = pd.DataFrame(cut_bin, columns=["col"])
        result_df = intervals_df.rolling(window=2).apply(lambda x: list(x)).dropna()
        clauses = []
        for interval in result_df["col"].tolist():
            clauses.append([GreaterThan(feature, interval[0], True), LowerThan(feature, interval[1], True)])

        slice_candidates = [QueryBasedSliceFunction(Query(clause)) for clause in clauses]

        # Filter by relevance
        # filt = SignificanceFilter(target)
        # slices = filt.filter(slice_candidates)

        return slice_candidates
