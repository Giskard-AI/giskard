from typing import Optional, Dict, List, Any, Iterable

import numpy as np
import pandas as pd

NaN = float('NaN')


def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


class ModelCache:
    # @TODO: improve this
    prediction_cache: Dict[str, Any]

    vectorized_get_cache_or_na = None

    def __init__(self, cache: Optional[pd.DataFrame] = None):
        cache = cache if cache is not None else pd.DataFrame(data={}, index=[])

        self.prediction_cache = cache.to_dict()

        self.vectorized_get_cache_or_na = np.vectorize(self.get_cache_or_na, otypes=[object])

    def get_cache_or_na(self, key: str):
        try:
            return self.prediction_cache.__getitem__(key)
        except KeyError:
            return NaN

    def read_from_cache(self, keys: pd.Series):
        return pd.Series(self.vectorized_get_cache_or_na(keys), index=keys.index)

    def set_cache(self, keys: pd.Series, values: List[Any]):
        for i in range(len(keys)):
            self.prediction_cache[keys.iloc[i]] = values[i]

    def to_df(self):
        index = [key for key, values in self.prediction_cache.items()]
        data = np.array([list(flatten([values])) for key, values in self.prediction_cache.items()])

        if len(data) > 0:
            return pd.DataFrame(data, index=index)
        else:
            return pd.DataFrame({})
