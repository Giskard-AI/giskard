# @TODO: simplify this module, don’t need this complexity.
import itertools
from collections import defaultdict
from typing import Sequence

import numpy as np
import pandas as pd

from ..core.core import DatasetProcessFunctionMeta
from ..ml_worker.testing.registry.registry import get_object_uuid
from ..ml_worker.testing.registry.slicing_function import SlicingFunction


def escape(value) -> str:
    return str(value) if type(value) is not str else "%s" % value


class Clause:
    def init_code(self):
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
        return self.to_pandas()

    def to_pandas(self):
        val = f"'{self.value}'" if isinstance(self.value, str) else self.value
        return f"`{self.column}` {self.operator} {val}"

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, {repr(self.value)}, equal={repr(self.equal)})"


class StringContains(Clause):
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __repr__(self) -> str:
        return f"<Clause ('{self.value}' in `{self.column}`)>"

    def __str__(self) -> str:
        return f"{self.column} contains '{self.value}'"

    def to_pandas(self):
        value = self.value.lower().replace("'", "\\'")
        return f"`{self.column}`.str.lower().str.contains('{value}')"

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, {repr(self.value)})"


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

    def __str__(self) -> str:
        return " & ".join([str(c) for c in self.get_all_clauses()])

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}([{', '.join([clause.init_code() for clause in self.get_all_clauses()])}])"


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


class QueryBasedSliceFunction(SlicingFunction):
    query: Query

    def __init__(self, query: Query):
        super().__init__(None, row_level=False, cell_level=False)
        self.query = query
        self.meta = DatasetProcessFunctionMeta(type='SLICE', no_code=True)
        self.meta.uuid = get_object_uuid(query)
        self.meta.code = self.query.init_code()
        self.meta.name = str(self)
        self.meta.display_name = str(self)
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = 'Automatically generated slicing function'

    def execute(self, data: pd.DataFrame):
        return self.query.run(data)

    def __str__(self):
        return str(self.query)

    def _should_save_locally(self) -> bool:
        return True

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({self.query.init_code()})"
