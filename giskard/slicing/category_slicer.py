from .base import BaseSlicer
from .slice import EqualTo, Query, QueryBasedSliceFunction


class CategorySlicer(BaseSlicer):
    def find_slices(self, features, target=None):
        data = self.dataset.df
        target = target or self.target

        if len(features) > 1:
            raise NotImplementedError("Only single-feature slicing is implemented for now.")
        (feature,) = features

        # Make slices
        values = data[feature].dropna().unique().tolist()
        slice_candidates = [QueryBasedSliceFunction(Query([EqualTo(feature, val)])) for val in values]

        return slice_candidates
