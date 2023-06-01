import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Sequence
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree._tree import Tree as SklearnTree
from sklearn.model_selection import GridSearchCV, train_test_split

from .base import BaseSlicer
from .slice import DataSlice, Query, LowerThan, GreaterThan
from .filters import SignificanceFilter


def make_slices_from_tree(
    data: pd.DataFrame, tree: SklearnTree, feature_names: Optional[Sequence] = None
):
    """Builds data slices from a decision tree."""
    node_clauses = np.empty(tree.node_count, dtype=list)
    node_clauses[0] = []

    queue = [0]
    while queue:
        cnode = queue.pop()

        left_child = tree.children_left[cnode]
        right_child = tree.children_right[cnode]

        if left_child < 0:  # leaf node, skip
            continue

        current_clauses = node_clauses[cnode]
        th = tree.threshold[cnode]
        feat = (
            tree.feature[cnode]
            if feature_names is None
            else feature_names[tree.feature[cnode]]
        )
        node_clauses[left_child] = current_clauses + [LowerThan(feat, th)]
        node_clauses[right_child] = current_clauses + [GreaterThan(feat, th, True)]

        queue.extend([left_child, right_child])

    # Now aggregate the filters for the leaves
    leaves_clauses = node_clauses[tree.children_left == -1]

    return [
        DataSlice(Query(clauses, optimize=True), data) for clauses in leaves_clauses
    ]


class DecisionTreeSlicer(BaseSlicer):
    def __init__(self, data=None, features=None, target=None):
        self.data = data
        self.features = features
        self.target = target

    def find_slices(self, features, target=None):
        target = target or self.target

        if len(features) > 1:
            raise NotImplementedError(
                "Only single-feature slicing is implemented for now."
            )

        data = self.data.loc[:, features + [target]].dropna()

        criterion = self._choose_tree_criterion(self.data.loc[:, target].values)
        logging.debug(f"Using `{criterion}` criterion")

        min_samples = max(int(0.01 * len(data)), 30)  # min 1% of the data or 30 samples
        data_var = data.loc[:, target].var()

        dt = DecisionTreeRegressor(
            criterion=criterion,
            splitter="best",
            min_samples_leaf=min_samples,
            max_leaf_nodes=20,
        )
        gs = GridSearchCV(
            dt,
            {
                # impurity in this case refers to the regression criterion
                "min_impurity_decrease": np.linspace(data_var / 100, data_var / 10, 10)
            },
        )
        gs.fit(data.loc[:, features], data.loc[:, target])
        dt = gs.best_estimator_

        # Need at least a split, otherwise return now.
        if dt.tree_.node_count < 2:
            logging.debug("No split found, stopping now.")
            return []

        # Debugging info
        corr = stats.pearsonr(data.loc[:, target], dt.predict(data.loc[:, features]))[0]
        logging.debug(f"Decision tree target correlation: {corr:.2f}")

        # Make test slices
        slice_candidates = make_slices_from_tree(data, dt.tree_, features)

        # Filter by relevance
        filt = SignificanceFilter(target)
        slices = filt.filter(slice_candidates)

        for s in slices:
            s.bind(self.data)

        return slices

    def _choose_tree_criterion(self, target_samples: np.ndarray):
        norm_ks_stat = stats.kstest(target_samples, "norm").statistic
        expon_ks_stat = stats.kstest(target_samples, "expon").statistic

        if norm_ks_stat <= expon_ks_stat:
            return "friedman_mse"

        if np.all(target_samples >= 0):
            return "poisson"

        return "squared_error"
