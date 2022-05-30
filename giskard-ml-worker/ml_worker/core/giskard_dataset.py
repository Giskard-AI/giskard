from io import BytesIO
from typing import Mapping, Callable

import pandas as pd
from ai_inspector.io_utils import decompress

from ml_worker_pb2 import SerializedDataWithMeta


class GiskardDataset:
    target: str
    feature_types: Mapping[str, str]
    df: pd.DataFrame

    def __init__(self, df: pd.DataFrame, target: str, feature_types: Mapping[str, str]) -> None:
        self.df = df
        self.target = target
        self.feature_types = feature_types

    @classmethod
    def from_serialized_with_meta(cls, df_with_meta: SerializedDataWithMeta):
        df = pd.read_csv(BytesIO(decompress(df_with_meta.serialized_df))) if df_with_meta.serialized_df else None
        target = df_with_meta.meta.target or None
        feature_types = df_with_meta.meta.feature_types or None
        return cls(df, target, feature_types)

    def slice(self, slice_fn: Callable):
        return GiskardDataset(self.df[slice_fn(self.df)], self.target, self.feature_types)

    def __len__(self):
        return len(self.df)
