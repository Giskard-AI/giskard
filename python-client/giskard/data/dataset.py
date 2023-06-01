# @TODO: this is TEMPORARY and will be removed soon!

import pandas as pd
from copy import deepcopy


class Dataset:
    def __init__(self, df: pd.DataFrame, target_col=None, class_labels=None, column_types=None, meta=None):
        self._df = df
        self.target_col = target_col
        self.class_labels = class_labels
        self._meta = meta if meta is not None else pd.DataFrame(index=self._df.index)
        self.column_types = column_types
    
    def to_giskard(self):
        from giskard import dataset
        return dataset(self.df(), target=self.target_col, column_types=self.column_types)

    def copy(self):
        return Dataset(
            self._df.copy(),
            self.target_col,
            deepcopy(self.class_labels),
            meta=self._meta.copy(),
        )

    @property
    def columns(self):
        return self._df.columns

    @property
    def target(self):
        return self._df.loc[:, self.target_col]

    def df(self, with_meta=False):
        if with_meta:
            return self._df.join(self._meta.add_prefix("meta__"), how="left")
        return self._df

    def meta(self):
        return self._meta

    def select_columns(self, columns=None, col_type=None, target=False):
        df = self._df.copy()

        # Filter by columns
        if columns is not None:
            df = df.loc[:, columns]

        # Filter by type
        if col_type is not None:
            df = df.select_dtypes(include=col_type)

        # Load target if needed
        if target:
            df[self.target_col] = self._df.loc[:, self.target_col]

        # Return new instance
        return Dataset(
            df, self.target_col, deepcopy(self.class_labels), meta=self._meta.copy()
        )

    def add_column(self, name, values):
        self._df[name] = values

    def add_meta_column(self, name, values):
        self._meta[name] = values

    def drop_meta_column(self, name):
        self._meta.drop(columns=[name], inplace=True)
