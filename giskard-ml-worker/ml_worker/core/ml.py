from typing import Optional, Union, Dict, Any

import numpy
from ai_inspector import ModelInspector
from pydantic import BaseModel
import pandas as pd


def select_single_prediction(probabilities, labels, threshold=None):
    if threshold is not None and len(labels) == 2:
        return labels[1] if probabilities[labels[1]] >= threshold else labels[0]
    else:
        return max(probabilities, key=lambda key: probabilities[key])


def run_predict(input_df: pd.DataFrame, model_inspector: ModelInspector):
    raw_prediction = model_inspector.prediction_function(input_df[model_inspector.input_types.keys()])
    if model_inspector.prediction_task == "regression":
        result = ModelPredictionResults(
            prediction=raw_prediction,
            raw_prediction=raw_prediction
        )
    elif model_inspector.prediction_task == "classification":
        labels = numpy.array(model_inspector.classification_labels)
        threshold = model_inspector.classification_threshold

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
            f"Prediction task is not supported: {model_inspector.prediction_task}"
        )
    return result


class ModelPredictionResults(BaseModel):
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class ModelPredictionResultsDTO(BaseModel):
    prediction: Any
    probabilities: Optional[Any]
