import csv
import os
from pathlib import Path
from typing import Dict, List, Any, Iterable, Optional

import numpy as np
import pandas as pd

from giskard.settings import settings

NaN = float('NaN')

CACHE_CSV_FILENAME = "giskard-model-cache.csv"


def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


class ModelCache:
    id: Optional[str] = None
    prediction_cache: Dict[str, Any] = None

    vectorized_get_cache_or_na = None

    def __init__(self, id: Optional[str] = None):
        self.id = id

        if id is not None:
            local_dir = Path(settings.home_dir / settings.cache_dir / "global/prediction_cache" / id)
            if local_dir.exists():
                with open(local_dir / CACHE_CSV_FILENAME, "r") as pred_f:
                    reader = csv.reader(pred_f)
                    self.prediction_cache = dict(reader)

        if self.prediction_cache is None:
            self.prediction_cache = {}

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

        if self.id:
            with open(Path(settings.home_dir / settings.cache_dir / "global/prediction_cache" / str(
                    self.id) / CACHE_CSV_FILENAME),
                      "a") as pred_f:
                writer = csv.writer(pred_f)
                for i in range(len(keys)):
                    writer.writerow([keys.iloc[i], values[i]])

    def _to_df(self):
        index = [key for key, values in self.prediction_cache.items()]
        data = np.array([list(flatten([values])) for key, values in self.prediction_cache.items()])

        if len(data) > 0:
            return pd.DataFrame(data, index=index)
        else:
            return pd.DataFrame({})

    def set_id(self, id: str):
        self.id = id

        if len(self.prediction_cache.keys()) > 0:
            local_dir = Path(settings.home_dir / settings.cache_dir / "global/prediction_cache" / id)
            os.makedirs(local_dir, exist_ok=True)
            with open(local_dir / CACHE_CSV_FILENAME, "w") as pred_f:
                writer = csv.writer(pred_f)
                for key, value in self.prediction_cache.items():
                    writer.writerow([key, value])
