import numpy as np

from .slice import GreaterThan, LowerThan
from .tree_slicer import DecisionTreeSlicer
from .opt_slicer import OptSlicer
from .multiscale_slicer import MultiscaleSlicer
from .bruteforce_slicer import BruteForceSlicer


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


def get_slicer(slicer_name, dataset, target):
    if slicer_name == "optimized":
        return OptSlicer(dataset, target=target)
    if slicer_name == "tree":
        return DecisionTreeSlicer(dataset, target=target)
    if slicer_name == "multiscale":
        return MultiscaleSlicer(dataset, target=target)
    if slicer_name == "bruteforce":
        return BruteForceSlicer(dataset, target=target)

    raise ValueError(f"Invalid slicer `{slicer_name}`.")
