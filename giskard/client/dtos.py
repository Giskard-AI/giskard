from typing import Any, Dict, List, Optional

from pydantic import Field

from giskard.core.validation import ConfiguredBaseModel


class TestInputDTO(ConfiguredBaseModel):
    name: str
    value: str
    type: str
    params: List["TestInputDTO"] = Field(default_factory=list)
    is_alias: bool = False


class SuiteTestDTO(ConfiguredBaseModel):
    testUuid: str
    functionInputs: Dict[str, TestInputDTO]
    displayName: Optional[str] = None


class TestSuiteDTO(ConfiguredBaseModel):
    name: Optional[str]
    project_key: str
    tests: List[SuiteTestDTO]
    function_inputs: List[TestInputDTO]


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
    functionInputs: List
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
