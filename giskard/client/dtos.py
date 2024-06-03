from typing import Any, Dict, List, Optional

from pydantic import Field

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


class ServerInfo(ConfiguredBaseModel):
    instanceId: Optional[str] = None
    serverVersion: Optional[str] = None
    instanceLicenseId: Optional[str] = None
    user: Optional[str] = None


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
