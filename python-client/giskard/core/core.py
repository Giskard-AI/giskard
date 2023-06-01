import types
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List


class SupportedModelTypes(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class SupportedColumnMeanings(Enum):
    NUMERIC = "numeric"
    CATEGORY = "category"
    TEXT = "text"


@dataclass
class ModelMeta:
    name: Optional[str]
    model_type: SupportedModelTypes
    feature_names: List[str]
    classification_labels: List[str]
    classification_threshold: float


@dataclass
class DatasetMeta:
    name: Optional[str]
    target: str
    column_meanings: Dict[str, str]
    column_types: Dict[str, str]


@dataclass
class TestFunctionArgument:
    name: str
    type: str
    default: any
    optional: bool


@dataclass
class TestFunctionMeta:
    code: str
    uuid: str
    name: str
    display_name: str
    module: str
    doc: str
    module_doc: str
    fn: types.FunctionType
    args: Dict[str, TestFunctionArgument]
    tags: List[str]
    version: Optional[int]
