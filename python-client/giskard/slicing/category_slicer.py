from sklearn.tree._tree import Tree as SklearnTree
from sklearn.model_selection import train_test_split

from .base import BaseSlicer
from .slice import DataSlice, Query, EqualTo, QueryBasedSliceFunction
from .filters import SignificanceFilter


class CategorySlicer(BaseSlicer):
    def find_slices(self, features, target=None):
        data = self.dataset.df
        target = target or self.target

        if len(features) > 1:
            raise NotImplementedError("Only single-feature slicing is implemented for now.")
        (feature,) = features

        # Make slices
        values = data[feature].unique().tolist()
        slice_candidates = [QueryBasedSliceFunction(Query([EqualTo(feature, val)])) for val in values]

        return slice_candidates
