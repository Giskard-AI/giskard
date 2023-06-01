import itertools
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import Sequence

from ..ml_worker.testing.registry.slice_function import SliceFunction

# @TODO: simplify this module, don’t need this complexity.


class Clause:
    pass


class ComparisonClause(Clause):
    _operator: str

    def __init__(self, column, value, equal=False):
        self.column = column
        self.value = value
        self.equal = equal

    @property
    def operator(self):
        return self._operator + ("=" if self.equal else "")

    def __repr__(self) -> str:
        return f"<Clause (`{self.column}` {self.operator} {self.value})>"

    def __str__(self) -> str:
        return self.__repr__()

    def to_pandas(self):
        val = f"'{self.value}'" if isinstance(self.value, str) else self.value
        return f"{self.column} {self.operator} {val}"


class StringContains(Clause):
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __repr__(self) -> str:
        return f"<Clause ('{self.value}' in `{self.column}`)>"

    def to_pandas(self):
        value = self.value.lower().replace("'", "\\'")
        return f"{self.column}.str.lower().str.contains('{value}')"


class GreaterThan(ComparisonClause):
    _operator = ">"


class LowerThan(ComparisonClause):
    _operator = "<"


class EqualTo(ComparisonClause):
    _operator = "=="


class Query:
    clauses: defaultdict

    def __init__(self, clauses, optimize=False):
        self.clauses = defaultdict(list)
        for clause in clauses:
            self.clauses[clause.column].append(clause)

        if optimize:
            self.optimize()

    def optimize(self):
        # Aggregate comparison Clauses
        for column, clauses in self.clauses.items():
            self.clauses[column] = _optimize_column_clauses(clauses)

    def add(self, clause: Clause):
        self.clauses[clause.column].append(clause)

        return self

    def columns(self):
        return list(self.clauses.keys())

    def get_all_clauses(self):
        return list(itertools.chain(*self.clauses.values()))

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(self.clauses) < 1:
            return df

        return df.query(self.to_pandas())

    def mask(self, df: pd.DataFrame):
        if len(self.clauses) < 1:
            return pd.Series(np.ones(len(df), dtype=bool), index=df.index)

        return df.eval(self.to_pandas())

    def to_pandas(self):
        return " & ".join([c.to_pandas() for c in self.get_all_clauses()])


def _optimize_column_clauses(clauses: Sequence[Clause]):
    if len(clauses) < 2:
        return clauses

    # Check correct execution
    assert all(c.column == clauses[0].column for c in clauses)

    conds = defaultdict(list)
    for clause in clauses:
        conds[clause.__class__].append(clause)

    # Keep the best comparison clauses
    def map_to_order(c):
        return c.value, c.equal

    if GreaterThan in conds:
        conds[GreaterThan] = [max(conds[GreaterThan], key=map_to_order)]
    if LowerThan in conds:
        conds[LowerThan] = [min(conds[LowerThan], key=map_to_order)]

    return list(itertools.chain(*conds.values()))


class DataSlice:
    def __init__(self, query: Query, raw_data=None):
        self.query = query
        data = raw_data if raw_data is not None else pd.DataFrame(columns=query.columns())
        self.bind(data)

    def bind(self, data: pd.DataFrame):
        self._data = data
        self.mask = self.query.mask(self._data)

    @property
    def data(self):
        return self._data[self.mask]

    @property
    def data_complement(self):
        return self._data[~self.mask]

    @property
    def data_unsliced(self):
        return self._data

    def columns(self):
        return self.query.columns()

    def get_column_interval(self, column):
        assert column in self.columns(), f"Column `{column}` is not present in the slice."

        clauses = self.query.clauses[column]

        try:
            low = max(c.value for c in clauses if isinstance(c, GreaterThan))
        except (StopIteration, ValueError):
            low = None

        try:
            high = min(c.value for c in clauses if isinstance(c, LowerThan))
        except (StopIteration, ValueError):
            high = None

        return low, high

    def __len__(self):
        return len(self.data)


class QueryBasedSliceFunction(SliceFunction):
    row_level = False

    def __init__(self, query: Query):
        self.query = query

    def __call__(self, data: pd.DataFrame):
        return self.query.run(data)
