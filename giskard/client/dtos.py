from typing import Dict, List, Optional

from giskard.core.validation import ConfiguredBaseModel


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
