from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

class SupportedModelTypes(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class SupportedFeatureTypes(Enum):
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
    loader_module: str
    loader_class: str


@dataclass
class DatasetMeta:
    name: Optional[str]
    target: str
    feature_types: Dict[str, str]
    column_types: Dict[str, str]
