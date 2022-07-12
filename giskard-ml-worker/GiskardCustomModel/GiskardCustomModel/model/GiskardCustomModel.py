from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.utils.validation import check_is_fitted
from sklearn.utils.multiclass import unique_labels

def get_model_pipeline(cols, n_estimators, max_depth, random_state=None):
    clf = make_pipeline(
            ColumnTransformer(transformers=[("feature_selection", "passthrough", cols)]),
            GiskardCustomModel(random_state=random_state, n_estimators=n_estimators, max_depth=max_depth)
        )
    return clf 

class GiskardCustomModel(BaseEstimator, ClassifierMixin):
    def __init__(self, n_estimators, max_depth, random_state=None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self._rf = RandomForestClassifier(n_estimators=self.n_estimators, max_depth=self.max_depth, random_state=self.random_state)

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

        return y