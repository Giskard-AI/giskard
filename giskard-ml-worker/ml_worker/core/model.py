from typing import List, Any, Optional, Callable, Iterable, Union

import numpy
import pandas as pd
from builtins import Exception
from pydantic import BaseModel

from ml_worker.core.giskard_dataset import GiskardDataset


class ModelPredictionResults(BaseModel):
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class GiskardModel:
    def __init__(self,
                 prediction_function: Callable[[pd.DataFrame], Iterable[Union[str, float, int]]],
                 model_type: str,
                 feature_names: List[str],
                 classification_threshold: float = None,
                 classification_labels: List[str] = None,
                 ) -> None:
        self.prediction_function = prediction_function
        self.model_type = model_type
        self.classification_threshold = classification_threshold
        self.feature_names = feature_names
        self.classification_labels = classification_labels

    def run_predict(self, dataset: GiskardDataset):
        df = dataset.df.copy()
        try:
            df = df.astype(dataset.column_types)
        except Exception as e:
            raise ValueError("Failed to apply column types to dataset") from e
        if dataset.target and dataset.target in df.columns:
            df.drop(dataset.target, axis=1, inplace=True)
        if self.feature_names:
            df = df[self.feature_names]
        raw_prediction = self.prediction_function(df)
        if self.model_type == "regression":
            result = ModelPredictionResults(
                prediction=raw_prediction,
                raw_prediction=raw_prediction
            )
        elif self.model_type == "classification":
            labels = numpy.array(self.classification_labels)
            threshold = self.classification_threshold

            if threshold is not None and len(labels) == 2:
                predicted_lbl_idx = (raw_prediction[:, 1] > threshold).astype(int)
            else:
                predicted_lbl_idx = raw_prediction.argmax(axis=1)

            all_predictions = pd.DataFrame(raw_prediction, columns=labels)

            predicted_labels = labels[predicted_lbl_idx]
            probability = raw_prediction[range(len(predicted_lbl_idx)), predicted_lbl_idx]

            result = ModelPredictionResults(
                prediction=predicted_labels,
                raw_prediction=predicted_lbl_idx,
                probabilities=probability,
                all_predictions=all_predictions
            )
        else:
            raise ValueError(
                f"Prediction task is not supported: {self.model_type}"
            )
        return result
