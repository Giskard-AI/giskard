from sklearn.tree._tree import Tree as SklearnTree
from sklearn.model_selection import train_test_split

from .base import BaseSlicer
from .slice import DataSlice, Query, EqualTo
from .filters import SignificanceFilter


class CategorySlicer(BaseSlicer):
    def find_slices(self, features, target=None):
        target = target or self.target

        if len(features) > 1:
            raise NotImplementedError(
                "Only single-feature slicing is implemented for now."
            )
        (feature,) = features

        # Make slices
        values = self.data[feature].unique().tolist()

        slice_candidates = [
            DataSlice(Query([EqualTo(feature, val)]), self.data) for val in values
        ]

        # Filter by relevance
        filt = SignificanceFilter(target)
        slices = filt.filter(slice_candidates)

        for s in slices:
            s.bind(self.data)

        return slices
