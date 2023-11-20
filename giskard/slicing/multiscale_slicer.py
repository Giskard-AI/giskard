import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

from .slice import GreaterThan, LowerThan, Query, QueryBasedSliceFunction
from .tree_slicer import DecisionTreeSlicer


class MultiscaleSlicer(DecisionTreeSlicer):
    def find_slices(self, features, target=None):
        target = target or self.target
        data = self.dataset.df.loc[:, list(features) + [target]].dropna()
        min_leaf_size = 30

        if len(data) < 2 * min_leaf_size:
            return []

        # Adaptive binning via decision tree
        criterion = self._choose_tree_criterion(data.loc[:, target].values)
        dt = DecisionTreeRegressor(criterion=criterion, min_samples_leaf=min_leaf_size)
        dt.fit(data.loc[:, features], data[target])
        tree = dt.tree_

        # Global median
        global_med = data[target].median()

        # Start from the leaves and go up level by level
        dp = dt.decision_path(data.loc[:, features])

        leaf_bins = tree.apply(data.loc[:, features].values.astype(np.float32))
        dx_agg = data.loc[:, target].groupby(leaf_bins).median()
        deviant_leaves = dx_agg.index[dx_agg > global_med * (1 + self.min_deviation)]

        def get_parent(node):
            lp = np.nonzero(tree.children_left == node)[0]
            rp = np.nonzero(tree.children_right == node)[0]

            return np.concatenate((lp, rp))[0]

        def is_significant_slice(samples):
            return samples[target].median() > (1 + self.min_deviation) * global_med

        selection_nodes = []
        for node_id in deviant_leaves:
            depth = 0

            while node_id is not None:
                parent_id = get_parent(node_id)
                samples_idx = np.nonzero(dp[:, parent_id])[0]

                if is_significant_slice(data.iloc[samples_idx]):
                    node_id = parent_id
                    depth += 1
                else:
                    selection_nodes.append(
                        {
                            "node": node_id,
                            "depth": depth,
                        }
                    )
                    break

        if len(selection_nodes) == 0:
            return []

        # Keep slices that are consistent across 5 levels
        dx_sel = pd.DataFrame(selection_nodes).query("depth >= 3")

        # Reconstruct rules
        slices = []
        for node_id in dx_sel.node.unique():
            th_min = -float("inf")
            th_max = float("inf")

            while node_id != 0:
                parent_id = get_parent(node_id)

                th = tree.threshold[parent_id]
                if tree.children_left[parent_id] == node_id:
                    th_max = min(th_max, th)
                else:
                    th_min = max(th_min, th)

                node_id = parent_id

            clauses = []
            if np.isfinite(th_min):
                clauses.append(GreaterThan(features[0], th_min))
            if np.isfinite(th_max):
                clauses.append(LowerThan(features[0], th_max, True))

            slices.append(QueryBasedSliceFunction(Query(clauses)))

        return slices
