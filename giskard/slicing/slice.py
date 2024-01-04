# @TODO: simplify this module, don’t need this complexity.
from typing import Callable, Dict, List, Sequence

import itertools
import operator
import re
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np
import pandas as pd

from ..core.core import DatasetProcessFunctionMeta, DatasetProcessFunctionType
from ..registry.slicing_function import SlicingFunction
from ..utils.display import format_number


def escape(value) -> str:
    return str(value) if not isinstance(value, str) else "%s" % value


def _decode(series: pd.Series) -> pd.Series:
    return series.str.decode("utf-8").fillna(series)


class Clause(ABC):
    @abstractmethod
    def mask(self, df: pd.DataFrame) -> pd.Series:
        ...

    def __repr__(self) -> str:
        return f"<Clause {str(self)}>"

    @abstractmethod
    def to_clause(self):
        ...


class ComparisonClause(Clause, ABC):
    _operator: Callable

    def __init__(self, column, value):
        self.column = column
        self.value = value

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return self._operator(df[self.column], self.value)


class ContainsWord(Clause):
    def __init__(self, column, value, is_not: bool = False):
        self.column = column
        self.value = value
        self.is_not = is_not

    def __str__(self) -> str:
        return f"`{self.column}` {'does not contain' if self.is_not else 'contains'} \"{self.value}\""

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return _decode(df[self.column]).str.contains(rf"\b{re.escape(self.value)}\b", case=False).ne(self.is_not)

    def to_clause(self):
        return {
            "columnName": self.column,
            "comparisonType": "DOES_NOT_CONTAINS" if self.is_not else "CONTAINS",
            "value": self.value,
        }


class IsNa(Clause):
    def __init__(self, column, is_not: bool = False):
        self.column = column
        self.is_not = is_not

    def __str__(self) -> str:
        return f"`{self.column}` {'is not empty' if self.is_not else 'is empty'}"

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return df[self.column].isna().ne(self.is_not)

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, is_not={repr(self.is_not)})"

    def to_clause(self):
        return {
            "columnName": self.column,
            "comparisonType": "IS_NOT_EMPTY" if self.is_not else "IS_EMPTY",
            "value": None,
        }


class StartsWith(Clause):
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __str__(self) -> str:
        return f'`{self.column}` starts with "{self.value}"'

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return _decode(df[self.column]).str.lower().str.startswith(self.value.lower())

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, {repr(self.value)})"

    def to_clause(self):
        return {"columnName": self.column, "comparisonType": "STARTS_WITH", "value": self.value}


class EndsWith(Clause):
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __str__(self) -> str:
        return f'`{self.column}` ends with "{self.value}"'

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return _decode(df[self.column]).str.lower().str.endswith(self.value.lower())

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, {repr(self.value)})"

    def to_clause(self):
        return {"columnName": self.column, "comparisonType": "ENDS_WITH", "value": self.value}


class GreaterThan(ComparisonClause):
    def __init__(self, column, value, equal=False):
        super().__init__(column, value)
        self.equal = equal
        self._operator = operator.ge if equal else operator.gt

    def __str__(self) -> str:
        operator = ">=" if self.equal else ">"
        return f"`{self.column}` {operator} {_pretty_str(self.value)}"

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, {repr(self.value)}, equal={repr(self.equal)})"

    def to_clause(self):
        return {
            "columnName": self.column,
            "comparisonType": "GREATER_THAN_EQUALS" if self.equal else "GREATER_THAN",
            "value": self.value,
        }


class LowerThan(ComparisonClause):
    def __init__(self, column, value, equal=False):
        super().__init__(column, value)
        self.equal = equal
        self._operator = operator.le if equal else operator.lt

    def __str__(self) -> str:
        operator = "<=" if self.equal else "<"
        return f"`{self.column}` {operator} {_pretty_str(self.value)}"

    def init_code(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}({repr(self.column)}, {repr(self.value)}, equal={repr(self.equal)})"

    def to_clause(self):
        return {
            "columnName": self.column,
            "comparisonType": "LOWER_THAN_EQUALS" if self.equal else "LOWER_THAN",
            "value": self.value,
        }


class EqualTo(ComparisonClause):
    _operator = operator.eq

    def __str__(self) -> str:
        return f"`{self.column}` == {_pretty_str(self.value)}"

    def to_clause(self):
        return {"columnName": self.column, "comparisonType": "IS", "value": self.value}


class NotEqualTo(ComparisonClause):
    _operator = operator.ne

    def __str__(self) -> str:
        return f"`{self.column}` != {_pretty_str(self.value)}"

    def to_clause(self):
        return {"columnName": self.column, "comparisonType": "IS_NOT", "value": self.value}


def generate_clause(clause: Dict[str, str]) -> Clause:
    if clause["comparisonType"] == "IS":
        return EqualTo(clause["columnName"], clause["value"])
    elif clause["comparisonType"] == "IS_NOT":
        return NotEqualTo(clause["columnName"], clause["value"])
    elif clause["comparisonType"] == "CONTAINS":
        return ContainsWord(clause["columnName"], clause["value"], is_not=False)
    elif clause["comparisonType"] == "DOES_NOT_CONTAINS":
        return ContainsWord(clause["columnName"], clause["value"], is_not=True)
    elif clause["comparisonType"] == "STARTS_WITH":
        return StartsWith(clause["columnName"], clause["value"])
    elif clause["comparisonType"] == "ENDS_WITH":
        return EndsWith(clause["columnName"], clause["value"])
    elif clause["comparisonType"] == "GREATER_THAN_EQUALS":
        return GreaterThan(clause["columnName"], clause["value"], equal=True)
    elif clause["comparisonType"] == "GREATER_THAN":
        return GreaterThan(clause["columnName"], clause["value"])
    elif clause["comparisonType"] == "LOWER_THAN_EQUALS":
        return LowerThan(clause["columnName"], clause["value"], equal=True)
    elif clause["comparisonType"] == "LOWER_THAN":
        return LowerThan(clause["columnName"], clause["value"])
    elif clause["comparisonType"] == "IS_EMPTY":
        return IsNa(clause["columnName"], is_not=False)
    elif clause["comparisonType"] == "IS_NOT_EMPTY":
        return IsNa(clause["columnName"], is_not=True)
    else:
        raise TypeError(f"The comparison clause of type {clause['comparisonType']} does not exist")


class Query:
    clauses: defaultdict

    def __init__(self, clauses, optimize=False):
        self.clauses = defaultdict(list)
        for clause in clauses:
            # if clause.value is an int64, convert it to an int
            if isinstance(clause.value, np.int64):
                clause.value = int(clause.value)
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

    def to_clauses(self):
        return [clause.to_clause() for clause in self.get_all_clauses()]

    @classmethod
    def from_clauses(cls, clauses: List[Dict[str, str]]):
        return cls([generate_clause(clause) for clause in clauses])


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
        self.meta = DatasetProcessFunctionMeta(type="SLICE", process_type=DatasetProcessFunctionType.CLAUSES)
        self.meta.clauses = self.query.to_clauses()
        self.meta.code = ""
        self.meta.name = str(self)
        self.meta.display_name = str(self)
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = self.meta.default_doc("Automatically generated slicing function")
        self.meta.uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, self.meta.name))

    def execute(self, data: pd.DataFrame):
        return self.query.run(data)

    def __str__(self):
        return str(self.query)


def _pretty_str(value):
    if isinstance(value, (float, int)):
        return format_number(value, 3)

    if isinstance(value, str):
        return f'"{value}"'

    return str(value)
