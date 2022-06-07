from io import BytesIO
from typing import Mapping, Callable, Optional

import pandas as pd
from ai_inspector.io_utils import decompress

from generated.ml_worker_pb2 import SerializedGiskardDataset


class GiskardDataset:
    target: str
    feature_types: Mapping[str, str]
    df: pd.DataFrame

    def __init__(self, df: pd.DataFrame, target: Optional[str], feature_types: Mapping[str, str]) -> None:
        self.df = df
        self.target = target
        self.feature_types = feature_types

    @classmethod
    def from_serialized(cls, serialized_ds: SerializedGiskardDataset):
        df = pd.read_csv(BytesIO(decompress(serialized_ds.serialized_df))) if serialized_ds.serialized_df else None
        target = serialized_ds.target or None
        feature_types = serialized_ds.feature_types or None
        return cls(df, target, feature_types)

    def slice(self, slice_fn: Callable):
        if slice_fn is None:
            return self
        return GiskardDataset(slice_fn(self.df), self.target, self.feature_types)

    def __len__(self):
        return len(self.df)
