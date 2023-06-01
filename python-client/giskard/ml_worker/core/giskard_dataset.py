from typing import Callable, Dict, Optional

import pandas as pd


class GiskardDataset:
    target: str
    feature_types: Dict[str, str]
    column_types: Dict[str, str]
    df: pd.DataFrame

    def __init__(
        self,
        df: pd.DataFrame,
        target: Optional[str],
        feature_types: Dict[str, str],
        column_types: Dict[str, str] = None,
    ) -> None:
        self.df = df
        self.target = target
        self.feature_types = feature_types
        self.column_types = column_types

    @property
    def columns(self):
        return self.df.columns

    def slice(self, slice_fn: Callable):
        if slice_fn is None:
            return self
        return GiskardDataset(slice_fn(self.df), self.target, self.feature_types)

    def __len__(self):
        return len(self.df)
