from typing import Any, Optional

import pydantic


# @TODO: Define the fields of this class more rigorously.
class ModelPredictionResults(pydantic.BaseModel):
    """Data structure for model predictions.

    For regression models, the `prediction` field of the returned `ModelPredictionResults` object will contain the same
    values as the `raw_prediction` field.

    For binary or multiclass classification models, the `prediction` field of the returned `ModelPredictionResults`
    object will contain the predicted class labels for each example in the input dataset. The `probabilities` field
    will contain the predicted probabilities for the predicted class label. The `all_predictions` field will contain
    the predicted probabilities for all class labels for each example in the input dataset.

    Attributes
    ----------
    raw : Any, optional
        The predicted probabilities.
    prediction : Any, optional
        The predicted class labels for each example in the input dataset.
    raw_prediction : Any, optional
        The predicted class label.
    probabilities : Any, optional
        The predicted probabilities for the predicted class label.
    all_predictions : Any, optional
        The predicted probabilities for all class labels for each example in the input dataset.
    """

    raw: Any = []
    prediction: Any = []
    raw_prediction: Any = []
    probabilities: Optional[Any]
    all_predictions: Optional[Any]
