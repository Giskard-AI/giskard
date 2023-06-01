import numpy as np

from .slice import GreaterThan, LowerThan


def get_slice_feature_interval(data_slice, feature, min_value=None, max_value=None):
    clauses = data_slice.query.clauses[feature]
    try:
        low = next(c for c in clauses if isinstance(c, GreaterThan)).threshold
    except StopIteration:
        low = min_value or -float("inf")

    try:
        high = next(c for c in clauses if isinstance(c, LowerThan)).threshold
    except StopIteration:
        high = max_value or float("inf")

    return low, high


def get_slice_feature_intervals(slices, *args, **kwargs):
    return np.array([get_slice_feature_interval(s, *args, **kwargs) for s in slices])
