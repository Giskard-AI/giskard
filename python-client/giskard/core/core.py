from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Union, Literal


class SupportedModelTypes(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


ModelType = Union[SupportedModelTypes, Literal["classification", "regression"]]


class SupportedColumnTypes(Enum):
    NUMERIC = "numeric"
    CATEGORY = "category"
    TEXT = "text"


ColumnType = Union[SupportedColumnTypes, Literal["numeric", "category", "text",]]


@dataclass
class ModelMeta:
    name: Optional[str]
    model_type: SupportedModelTypes
    feature_names: List[str]
    classification_labels: List[str]
    classification_threshold: float
    loader_module: str
    loader_class: str


@dataclass
class DatasetMeta:
    name: Optional[str]
    target: str
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]
