from typing import Optional, Dict, List, Any

import numpy as np
import pandas as pd

NaN = float('NaN')


class ModelCache:
    prediction_cache: Dict[str, Any]
    classification_labels: List[str]

    vectorized_get_cache_or_na = None
    nan_val = None

    def __init__(self, cache: Optional[pd.DataFrame] = None, classification_labels: Optional[List[str]] = None):
        cache = cache if cache is not None else pd.DataFrame(data={}, index=[])

        self.prediction_cache = cache.to_dict()
        self.classification_labels = [
            'raw_prediction'] if classification_labels is None else classification_labels.copy()

        self.nan_val = NaN if len(self.classification_labels) == 1 else np.full(shape=len(self.classification_labels),
                                                                                fill_value=NaN)

        self.vectorized_get_cache_or_na = np.vectorize(self.get_cache_or_na, otypes=[object])

    def get_cache_or_na(self, key: str):
        try:
            return self.prediction_cache.__getitem__(key)
        except KeyError:
            return self.nan_val

    def read_from_cache(self, keys: pd.Series):
        return np.array(list(self.vectorized_get_cache_or_na(keys)))

    def set_cache(self, keys: pd.Series, values: List[Any]):
        for i in range(len(keys)):
            self.prediction_cache[keys.iloc[i]] = values[i]

    def to_df(self):
        is_array = len(self.classification_labels) > 1
        data = np.array(
            [[key] + list(values) if is_array else [key, values] for key, values in self.prediction_cache.items()])

        if len(data) > 0:
            return pd.DataFrame([data[:, i + 1] for i in range(len(self.classification_labels))],
                                columns=self.classification_labels, index=data[:, 0])
        else:
            return pd.DataFrame({})
