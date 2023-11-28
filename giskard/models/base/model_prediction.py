from typing import Any, Optional

from pydantic import Field

from giskard.core.validation import ConfiguredBaseModel


# @TODO: Define the fields of this class more rigorously.
class ModelPredictionResults(ConfiguredBaseModel):
    """Data structure for model predictions.

    For regression models, the `prediction` field of the returned `ModelPredictionResults` object will contain the same
    values as the `raw_prediction` field.

    For binary or multiclass classification models, the `prediction` field of the returned `ModelPredictionResults`
    object will contain the predicted class labels for each example in the input dataset. The `probabilities` field
    will contain the predicted probabilities for the predicted class label. The `all_predictions` field will contain
    the predicted probabilities for all class labels for each example in the input dataset.

    Attributes
    ----------
    raw : Optional[Any]
        The predicted probabilities.
    prediction : Optional[Any]
        The predicted class labels for each example in the input dataset.
    raw_prediction : Optional[Any]
        The predicted class label.
    probabilities : Optional[Any]
        The predicted probabilities for the predicted class label.
    all_predictions : Optional[Any]
        The predicted probabilities for all class labels for each example in the input dataset.
    """

    raw: Any = Field(default_factory=list)
    prediction: Any = Field(default_factory=list)
    raw_prediction: Any = Field(default_factory=list)
    probabilities: Optional[Any] = None
    all_predictions: Optional[Any] = None
