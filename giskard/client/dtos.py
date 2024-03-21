from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

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

# ListInfo are list of dictionaries representing a table (used to minimize data size by reducing redundancy of keys)
# Example:
# {'threshold_range': {'min': ['10', '15'], 'max': ['20', '20' }, 'value': ['15', '12'], 'status': ['PASSED', 'FAILED']}
SimpleColumnListInfo = List[Optional[str]]
ColumnGroupListInfo = Dict[str, SimpleColumnListInfo]


class DataTable(ConfiguredBaseModel):
    columns: Dict[str, Union[ColumnGroupListInfo, SimpleColumnListInfo]]
    items: int

    def _append_to_column_group(self, key: str, record: ColumnGroupRecordInfo):
        existing = key in self.columns
        if not existing:
            self.columns[key] = dict()

        column_group = self.columns[key]
        if not isinstance(column_group, dict):
            raise ValueError(f"Mix of single items and dict for key {key}")

        missing_columns = set(column_group.keys())

        for key, value in record.items():
            if key in column_group:
                column_group[key].append(record)
                missing_columns.remove(key)
            else:
                column_group[key] = [None] * self.items + [record]

        for missing_column in missing_columns:
            column_group[missing_column].append(None)

        return existing

    def _append_to_column(self, key: str, record: SimpleColumnRecordInfo):
        existing = key in self.columns
        if not existing:
            self.columns[key] = [None] * self.items

        column = self.columns[key]
        if not isinstance(column, list):
            raise ValueError(f"Mix of single items and dict for key {key}")

        column.append(record)

        return existing

    def append(self, record: DataTableRecord):
        missing_columns = set(self.columns.keys())

        for key, value in record.items():
            if isinstance(value, dict):
                to_remove = self._append_to_column_group(key, value)
            else:
                to_remove = self._append_to_column_group(key, value)

            if to_remove:
                missing_columns.remove(key)

        for missing_column in missing_columns:
            column = self.columns[missing_column]

            if isinstance(column, list):
                column.append(None)
            else:
                for sub_column in column:
                    sub_column.append(None)

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
