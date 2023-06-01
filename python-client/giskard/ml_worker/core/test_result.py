from dataclasses import dataclass, field
from enum import Enum

from typing import List, Dict


class TestMessageLevel(Enum):
    ERROR = 1,
    INFO = 2


@dataclass
class TestMessage:
    type: TestMessageLevel
    text: str


@dataclass
class PartialUnexpectedCounts:
    value: List[int]
    count: int


@dataclass
class TestResult:
    passed: bool = False
    messages: List[TestMessage] = field(default_factory=list, repr=False)
    props: Dict[str, str] = field(default_factory=dict, repr=False)
    metric: float = 0
    missing_count: int = 0
    missing_percent: float = 0
    unexpected_count: int = 0
    unexpected_percent: float = 0
    unexpected_percent_total: float = 0
    unexpected_percent_nonmissing: float = 0
    partial_unexpected_index_list: List[PartialUnexpectedCounts] = field(default_factory=list, repr=False)
    unexpected_index_list: List[int] = field(default_factory=list, repr=False)
    output_df: bytes = None
    number_of_perturbed_rows: int = 0
    actual_slices_size: List[int] = field(default_factory=list, repr=False)
    reference_slices_size: List[int] = field(default_factory=list, repr=False)
