"""
Trigger functions for model debugging prediction notifications.

Functions:

- create_overconfidence_push: Create overconfidence notification from model prediction.
- create_borderline_push: Create borderline/underconfidence notification from prediction.

"""
import pandas as pd

from giskard.datasets.base import Dataset
from giskard.models.base.model import BaseModel
from giskard.testing.tests.calibration import (
    test_overconfidence_rate,
    test_underconfidence_rate,
)

from ..push import BorderlinePush, OverconfidencePush


def create_overconfidence_push(model: BaseModel, ds: Dataset, df: pd.DataFrame) -> OverconfidencePush:
    """
    Create overconfidence notification from model prediction.

    Checks if model is overconfident on a given row based on
    overconfidence rate test.

    If overconfidence detected and predicted class is incorrect,
    creates and returns OverconfidencePush.

    Args:
        model (BaseModel): Giskard model
        ds (Dataset): Original dataset
        df (pd.DataFrame): DataFrame with row to analyze

    Returns:
        OverconfidencePush if overconfidence and misprediction
        None otherwise
    """
    if model.is_classification:
        row_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)

        values = row_slice.df
        training_label = values[ds.target].values[0]
        model_prediction_results = model.predict(row_slice)
        training_label_proba = model_prediction_results.all_predictions[training_label].values[0]
        prediction = model_prediction_results.prediction[0]

        test_result = test_overconfidence_rate(model, row_slice).execute()
        if not test_result.passed and training_label != prediction:
            return OverconfidencePush(
                training_label, training_label_proba, row_slice, prediction, rate=test_result.metric
            )


def create_borderline_push(model: BaseModel, ds: Dataset, df: pd.DataFrame) -> BorderlinePush:
    """
    Create borderline/underconfidence notification from prediction.

    Checks if model is underconfident on a given row based on
    underconfidence rate test.

    If underconfidence detected, creates and returns BorderlinePush.

    Args:
        model (BaseModel): ML model
        ds (Dataset): Original dataset
        df (pd.DataFrame): DataFrame with row to analyze

    Returns:
        BorderlinePush if underconfident, None otherwise.
    """
    if model.is_classification:
        row_slice = Dataset(
            df=df,
            target=ds.target,
            column_types=ds.column_types.copy(),
            validation=False,
            name=f"One-Sample of <dataset:{ds.id}> for underconfidence test using <model:{model.id}>",
        )
        values = row_slice.df
        target_value = values[ds.target].values.item()
        prediction_results = model.predict(row_slice)
        target_value_proba = prediction_results.all_predictions[target_value].values.item()
        test_result = test_underconfidence_rate(model, row_slice).execute()
        if not test_result.passed:
            return BorderlinePush(target_value, target_value_proba, row_slice, rate=test_result.metric)
