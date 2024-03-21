from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

from abc import ABC
from enum import Enum

from pydantic import Field

from giskard.core.core import TestResultStatusEnum
from giskard.core.validation import ConfiguredBaseModel
from giskard.utils.artifacts import serialize_parameter

if TYPE_CHECKING:
    from giskard.llm.evaluators.base import EvaluationResult


class TestInputDTO(ConfiguredBaseModel):
    name: str
    value: str
    type: str
    params: List["TestInputDTO"] = Field(default_factory=list)
    is_alias: bool = False
    is_default_value: bool = False

    @classmethod
    def from_inputs_dict(cls, inputs: Dict[str, Any]) -> List["TestInputDTO"]:
        return [
            cls(name=name, value=str(serialize_parameter(value)), type=type(value).__qualname__)
            for name, value in inputs.items()
        ]


class SuiteTestDTO(ConfiguredBaseModel):
    id: Optional[int]
    testUuid: str
    functionInputs: Dict[str, TestInputDTO]
    displayName: Optional[str] = None


class TestSuiteDTO(ConfiguredBaseModel):
    name: Optional[str]
    project_key: str
    tests: List[SuiteTestDTO]
    function_inputs: List[TestInputDTO]


class TestSuiteExecutionResult(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    CANCELLED = "CANCELLED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


class MLWorkerWSTestMessageType(str, Enum):
    ERROR = "ERROR"
    INFO = "INFO"


class TestResultMessageDTO(ConfiguredBaseModel):
    type: MLWorkerWSTestMessageType
    text: str


class Column(ABC, ConfiguredBaseModel):
    pass


class SimpleColumn(Column):
    row_data: List[str]


class ColumnGroup(Column):
    columns: SimpleColumn


# Records are dictionaries of single table entry
# Example:
# [
# {'threshold_range': {'min': '10', 'max': '20'}, 'value': '15', 'status': 'PASSED'},
# {'threshold_range': {'min': '15', 'max': '20'}, 'value': '12', 'status': 'FAILED'}
# ]
SimpleColumnRecordInfo = Optional[str]
ColumnGroupRecordInfo = Dict[str, SimpleColumnRecordInfo]
DataTableRecord = Dict[str, Union[SimpleColumnRecordInfo, ColumnGroupRecordInfo]]


class DataTable(ConfiguredBaseModel):
    # Ordered list of header for each column
    columns: Dict[str, List[Optional[str]]]
    items: int

    def _append_value(self, path: str, item: SimpleColumnRecordInfo, missing_columns: Set[str]):
        if path not in self.columns:
            self.columns[path] = [None] * self.items + item
        else:
            self.columns[path].append(item)
            missing_columns.remove(path)

    def _append_dict(self, path: str, item: ColumnGroupRecordInfo, missing_columns: Set[str]):
        for key, value in item.items():
            if isinstance(value, dict):
                self._append_dict(f"{path}.{key}", value, missing_columns)
            else:
                self._append_value(path, value, missing_columns)

    def append(self, record: DataTableRecord):
        missing_columns = set(self.columns.keys())

        for key, value in record.items():
            if isinstance(value, dict):
                self._append_dict(key, value, missing_columns)
            else:
                self._append_value(key, value, missing_columns)

        for missing_column in missing_columns:
            self.columns[missing_column].append(None)

        self.items += 1

    @classmethod
    def from_records(cls, records: List[DataTableRecord]):
        data_table = cls(columns=[], items=0)

        for record in records:
            data_table.append(record)

        return data_table

    @classmethod
    def from_evaluation_result(cls, evaluation_result: EvaluationResult):
        return cls.from_records([result.to_dict() for result in evaluation_result.results])


class SaveSuiteTestExecutionDTO(ConfiguredBaseModel):
    suiteTest: SuiteTestDTO
    testUuid: str
    displayName: str
    inputs: Dict[str, str]
    arguments: Dict[str, TestInputDTO]
    messages: List[TestResultMessageDTO]
    status: TestResultStatusEnum
    metric: Optional[float]
    metricName: str
    failedIndexes: Dict[str, List[int]]
    evaluation_result: Optional[DataTable]


class SaveSuiteExecutionDTO(ConfiguredBaseModel):
    suiteId: Optional[int]
    label: str
    inputs: List[TestInputDTO]
    result: TestSuiteExecutionResult
    message: str
    results: List[SaveSuiteTestExecutionDTO]
    executionDate: str
    completionDate: str


class ServerInfo(ConfiguredBaseModel):
    instanceId: Optional[str] = None
    serverVersion: Optional[str] = None
    instanceLicenseId: Optional[str] = None
    user: Optional[str] = None


class TestInfo(ConfiguredBaseModel):
    testUuid: str
    functionInputs: Dict[str, Any]
    # The following inputs are never used and are here only for
    # coherence with backend
    id: int
    displayName: Optional[str]
    test: Any


class SuiteInfo(ConfiguredBaseModel):
    name: str
    tests: List[TestInfo]
    # The following inputs are never used and are here only for
    # coherence with backend
    id: int
    projectKey: str


class ModelMetaInfo(ConfiguredBaseModel):
    id: str
    name: str
    modelType: str
    featureNames: List[str]
    threshold: Optional[float] = None
    description: Optional[str] = None
    classificationLabels: Optional[List[str]] = None
    classificationLabelsDtype: Optional[str] = None
    languageVersion: str
    language: str
    createdDate: str
    size: int
    projectId: int


class DatasetMetaInfo(ConfiguredBaseModel):
    target: Optional[str] = None
    columnTypes: Dict[str, str]
    columnDtypes: Dict[str, str]
    numberOfRows: int
    categoryFeatures: Dict[str, List[str]]
    name: Optional[str] = None
    originalSizeBytes: int
    compressedSizeBytes: int
    createdDate: str
    id: str
