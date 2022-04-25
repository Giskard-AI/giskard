from typing import Optional, Union, Dict, List
from pydantic import BaseModel


class ModelMetadata(BaseModel):
    prediction_task: str
    input_types: Dict[str, str]
    classification_labels: Optional[List[str]]
    classification_threshold: Optional[float]


class ModelPredictionInput(BaseModel):
    features: Dict


class ModelExplanationResults(BaseModel):
    explanations: Union[Dict[str, float], Dict[str, Dict[str, float]]]
