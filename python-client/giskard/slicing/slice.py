# @TODO: simplify this module, don’t need this complexity.
import operator
import itertools
from collections import defaultdict
from abc import ABC, abstractmethod
from typing import Callable, Sequence
import re
import numpy as np
import pandas as pd

from ..core.core import DatasetProcessFunctionMeta
from ..ml_worker.testing.registry.registry import get_object_uuid
from ..ml_worker.testing.registry.slicing_function import SlicingFunction


class Clause(ABC):
    column: str

    @abstractmethod
    def mask(self, df: pd.DataFrame) -> pd.Series:
        ...

    def __repr__(self) -> str:
        return f"<Clause {str(self)}>"


class ComparisonClause(Clause):
    _operator: Callable

    def __init__(self, column, value):
        self.column = column
        self.value = value

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return self._operator(df[self.column], self.value)


class ContainsWord(Clause):
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __str__(self) -> str:
        return f"`{self.column}` contains \"{self.value}\""

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return df[self.column].str.contains(rf"\b{re.escape(self.value)}\b", case=False)


class GreaterThan(ComparisonClause):
    def __init__(self, column, value, equal=False):
        super().__init__(column, value)
        self.equal = equal
        self._operator = operator.ge if equal else operator.gt

    def __str__(self) -> str:
        operator = ">=" if self.equal else ">"
        return f"`{self.column}` {operator} {_pretty_str(self.value)}"


class LowerThan(ComparisonClause):
    def __init__(self, column, value, equal=False):
        super().__init__(column, value)
        self.equal = equal
        self._operator = operator.le if equal else operator.lt

    def __str__(self) -> str:
        operator = "<=" if self.equal else "<"
        return f"`{self.column}` {operator} {_pretty_str(self.value)}"


class EqualTo(ComparisonClause):
    _operator = operator.eq

    def __str__(self) -> str:
        return f"`{self.column}` == {_pretty_str(self.value)}"


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

        return df[self.mask(df)]

    def mask(self, df: pd.DataFrame):
        mask = pd.Series(np.ones(len(df), dtype=bool), index=df.index)
        for c in self.get_all_clauses():
            mask &= c.mask(df)
        return mask

    def __str__(self) -> str:
        return " AND ".join([str(c) for c in self.get_all_clauses()])


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
        self.meta = DatasetProcessFunctionMeta(type='SLICE')
        self.meta.uuid = get_object_uuid(query)
        self.meta.code = str(self)
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


def _pretty_str(value):
    if isinstance(value, float):
        return f"{value:.3f}"

    if isinstance(value, str):
        return f'"{value}"'

    return str(value)
