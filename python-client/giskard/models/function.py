from typing import Any, Callable, Iterable, Optional

import numpy
import pandas as pd

from ..core.core import ModelType
from ..core.validation import configured_validate_arguments
from .base.serialization import CloudpickleSerializableModel


class PredictionFunctionModel(CloudpickleSerializableModel):
    @configured_validate_arguments
    def __init__(
        self,
        model: Callable,
        model_type: ModelType,
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]] = None,
        model_postprocessing_function: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            model,
            model_type,
            data_preprocessing_function,
            model_postprocessing_function,
            name,
            feature_names,
            classification_threshold,
            classification_labels,
            id=id,
            **kwargs,
        )

    def model_predict(self, df: pd.DataFrame) -> numpy.ndarray:
        return self.model(df)
