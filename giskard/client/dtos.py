from typing import Any, Dict, List, Optional

from enum import Enum

from pydantic import Field

from giskard.core.core import TestResultStatusEnum
from giskard.core.validation import ConfiguredBaseModel
from giskard.utils.artifacts import serialize_parameter


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


class SaveSuiteTestExecutionDetailsDTO(ConfiguredBaseModel):
    inputs: Dict[str, List[str]]
    outputs: List[str]
    results: List[TestResultStatusEnum]
    metadata: Dict[str, List[str]]


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
    details: Optional[SaveSuiteTestExecutionDetailsDTO]


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
