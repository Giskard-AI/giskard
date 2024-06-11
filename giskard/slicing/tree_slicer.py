from typing import Optional, Sequence

import logging
import random

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.tree._tree import Tree as SklearnTree

from ..utils.analytics_collector import analytics
from .base import BaseSlicer
from .slice import GreaterThan, LowerThan, Query, QueryBasedSliceFunction

logger = logging.getLogger(__name__)


def make_slices_from_tree(tree: SklearnTree, feature_names: Optional[Sequence] = None):
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
        feat = tree.feature[cnode] if feature_names is None else feature_names[tree.feature[cnode]]
        node_clauses[left_child] = current_clauses + [LowerThan(feat, th)]
        node_clauses[right_child] = current_clauses + [GreaterThan(feat, th, True)]

        queue.extend([left_child, right_child])

    # Now aggregate the filters for the leaves
    leaves_clauses = node_clauses[tree.children_left == -1]

    return [QueryBasedSliceFunction(Query(clauses, optimize=True)) for clauses in leaves_clauses]


class DecisionTreeSlicer(BaseSlicer):
    def find_slices(self, features, target=None, min_samples=None):
        target = target or self.target
        data = self.dataset.df

        if len(features) > 1:
            raise NotImplementedError("Only single-feature slicing is implemented for now.")

        data = data.loc[:, features + [target]].dropna()

        min_samples = min_samples or max(int(0.01 * len(data)), 30)  # min 1% of the data or 30 samples

        if len(data) < min_samples:
            return []

        if pd.api.types.is_numeric_dtype(data[target]):
            logger.debug("Target is numeric, using regression tree.")
            criterion = self._choose_tree_criterion(data.loc[:, target].values)
            logger.debug(f"Using `{criterion}` criterion.")

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
        else:
            logger.debug("Target is not numeric, using a classification tree.")
            dt = DecisionTreeClassifier(
                criterion="gini",
                splitter="best",
                min_samples_leaf=min_samples,
                max_leaf_nodes=20,
                min_impurity_decrease=0,
            )
            dt.fit(data.loc[:, features], data.loc[:, target])

        # Need at least a split, otherwise return now.
        if dt.tree_.node_count < 2:
            logger.debug("No split found, stopping now.")
            return []

        # Telemetry (10% of samples)
        if random.random() < 0.1:
            try:
                analytics.track(
                    "scan:tree_slicer_params",
                    {
                        "n_samples": len(data),
                        "min_samples": min_samples,
                        "node_count": dt.tree_.node_count,
                        "impurity": dt.tree_.impurity.tolist(),
                        "class": dt.__class__.__name__,
                    },
                )
            except AttributeError:
                logger.debug("Error accessing tree parameters for analytics.")

        # Make test slices
        slice_candidates = make_slices_from_tree(dt.tree_, features)

        return slice_candidates

    def _choose_tree_criterion(self, target_samples: np.ndarray):
        norm_ks_stat = stats.kstest(target_samples, "norm").statistic
        expon_ks_stat = stats.kstest(target_samples, "expon").statistic

        if norm_ks_stat <= expon_ks_stat:
            return "friedman_mse"

        if np.all(target_samples >= 0):
            return "poisson"

        return "squared_error"
