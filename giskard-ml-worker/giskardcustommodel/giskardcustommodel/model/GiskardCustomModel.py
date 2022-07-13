from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.utils.multiclass import unique_labels
from sklearn.utils.validation import check_is_fitted


def get_model_pipeline(cols, n_estimators, max_depth, random_state=None):
    clf = make_pipeline(
        ColumnTransformer(transformers=[("feature_selection", "passthrough", cols)]),
        GiskardCustomModel(random_state=random_state, n_estimators=n_estimators, max_depth=max_depth,
                           feature_indexes=[0, 1])
    )
    return clf


class GiskardCustomModel(BaseEstimator, ClassifierMixin):
    def __init__(self, n_estimators, max_depth, feature_indexes, random_state=None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.feature_indexes = feature_indexes
        self._rf = RandomForestClassifier(n_estimators=self.n_estimators, max_depth=self.max_depth,
                                          random_state=self.random_state)
        print(f"Created with {feature_indexes} feature_indexes")

    def fit(self, X, y):
        self._classes = unique_labels(y)
        self._X = X
        self._y = y
        self._rf = self._rf.fit(X, y)

        return self

    def predict(self, X):
        check_is_fitted(self._rf)
        y = self._rf.predict(X)

        return y

    def predict_proba(self, X):
        check_is_fitted(self._rf)
        y = self._rf.predict_proba(X)

        mask = self.get_null_mask(X)
        for i, m in enumerate(mask):
            if m:
                y[i, :] = [1.0, 0.0]

        return y

    def get_null_mask(self, X):
        feature_to_mask = X[:, self.feature_indexes]
        mask = (feature_to_mask == 0).all(axis=1)
        return mask
