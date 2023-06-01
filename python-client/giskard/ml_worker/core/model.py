from typing import Any, Callable, Iterable, List, Optional, Union

import logging
from builtins import Exception

import numpy
import pandas as pd
from pydantic import BaseModel

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.utils.logging import Timer

logger = logging.getLogger(__name__)


class ModelPredictionResults(BaseModel):
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class GiskardModel:
    def __init__(
        self,
        prediction_function: Callable[[pd.DataFrame], Iterable[Union[str, float, int]]],
        model_type: str,
        feature_names: Optional[List[str]],
        classification_threshold: float = None,
        classification_labels: List[str] = None,
    ) -> None:
        self.prediction_function = prediction_function
        self.model_type = model_type
        self.classification_threshold = classification_threshold
        self.feature_names = feature_names
        self.classification_labels = classification_labels

    def run_predict(self, dataset: GiskardDataset):
        timer = Timer()
        df = self.prepare_dataframe(dataset)
        raw_prediction = self.prediction_function(df)
        if self.model_type == "regression":
            result = ModelPredictionResults(
                prediction=raw_prediction, raw_prediction=raw_prediction
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
                all_predictions=all_predictions,
            )
        else:
            raise ValueError(f"Prediction task is not supported: {self.model_type}")
        timer.stop(f"Predicted dataset with shape {dataset.df.shape}")
        return result

    def prepare_dataframe(self, dataset):
        df = dataset.df.copy()
        column_types = dict(dataset.column_types) if dataset.column_types else None
        if dataset.target:
            if dataset.target in df.columns:
                df.drop(dataset.target, axis=1, inplace=True)
            if column_types and dataset.target in column_types:
                del column_types[dataset.target]

        if self.feature_names:
            if set(self.feature_names) > set(df.columns):
                column_names = set(self.feature_names) - set(df.columns)
                raise ValueError(
                    f"The following columns are not found in the dataset: {', '.join(sorted(column_names))}"
                )
            df = df[self.feature_names]
            if column_types:
                column_types = {k: v for k, v in column_types.items() if k in self.feature_names}

        if column_types:
            df = self.cast_column_to_types(df, column_types)
        return df

    @staticmethod
    def cast_column_to_types(df, column_types):
        current_types = df.dtypes.apply(lambda x: x.name).to_dict()
        logger.info(f"Casting dataframe columns from {current_types} to {column_types}")
        if column_types:
            try:
                df = df.astype(column_types)
            except Exception as e:
                raise ValueError("Failed to apply column types to dataset") from e
        return df
