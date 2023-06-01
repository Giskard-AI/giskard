import tempfile
from typing import List, Iterable
import importlib
import numpy as np
import pandas as pd
from pandas.core.dtypes.common import is_string_dtype

from giskard.client.python_utils import warning
from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model
from giskard.core.validation import validate_is_pandasdataframe, validate_target
from giskard.ml_worker.core.dataset import Dataset


def validate_model(
        model: Model,
        validate_ds: Dataset
):
    model_type = model.meta.model_type

    loaded_model, loaded_data_prep_fn = validate_model_save_load(model)
    loader_class = getattr(importlib.import_module(model.meta.loader_module), model.meta.loader_class)
    model = loader_class(
        clf=loaded_model,
        data_preparation_function=loaded_data_prep_fn,
        model_type=model.meta.model_type,
        feature_names=model.meta.feature_names,
        classification_labels=model.meta.classification_labels,
        classification_threshold=model.meta.classification_threshold
    )
    if model.data_preparation_function is not None:
        validate_data_preparation_function(model.data_preparation_function)

    validate_classification_labels(model.meta.classification_labels, model_type)

    if model.is_classification:
        validate_classification_threshold_label(model.meta.classification_labels, model.meta.classification_threshold)

    assert model.meta.feature_names is None or isinstance(model.meta.feature_names, list), \
        "Invalid feature_names parameter. Please provide the feature names as a list."

    if validate_ds is not None:
        validate_is_pandasdataframe(validate_ds.df)
        validate_features(feature_names=model.meta.feature_names, validate_df=validate_ds.df)

        if model.is_regression:
            validate_model_execution(model, validate_ds)
        elif model.is_classification and validate_ds.target is not None:
            validate_target(validate_ds.target, validate_ds.df.keys())
            target_values = validate_ds.df[validate_ds.target].unique()
            validate_label_with_target(model.meta.classification_labels, target_values, validate_ds.target)
            validate_model_execution(model, validate_ds)
        else:  # Classification with target = None
            validate_model_execution(model, validate_ds)


def validate_model_execution(model: Model, dataset: Dataset) -> None:
    validation_size = min(len(dataset), 10)
    validation_ds = dataset.slice(lambda x: x.head(validation_size))
    try:
        prediction = model.predict(validation_ds)
    except Exception as e:
        raise ValueError("Invalid prediction_function input.\n" #TODO: Change prediction_function
                         "Please make sure that your_model.predict(dataset) does not return an error "
                         "message before uploading in Giskard") from e

    validate_deterministic_model(model, validation_ds, prediction)
    validate_prediction_output(validation_ds, model.meta.model_type, prediction.raw)
    if model.is_classification:
        validate_classification_prediction(model.meta.classification_labels, prediction.raw)


def validate_deterministic_model(model: Model, validate_ds: Dataset, prev_prediction):
    """
    Asserts if the model is deterministic by asserting previous and current prediction on same data
    """
    new_prediction = model.predict(validate_ds)

    if not np.allclose(prev_prediction.raw, new_prediction.raw):
        warning("Model is stochastic and not deterministic. Prediction function returns different results"
                "after being invoked for the same data multiple times.")


def validate_model_save_load(model: Model):
    """
    Validates if the model can be pickled and un-pickled using cloud pickle
    """
    try:
        loader_class = getattr(importlib.import_module(model.meta.loader_module), model.meta.loader_class)
        with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
            model.save_to_local_dir(f)
            model.save_data_preparation_function(f)
            loaded_model = loader_class.read_model_from_local_dir(f)
            loaded_data_prep_fn = loader_class.read_data_preparation_function_from_artifact(f)
            return loaded_model, loaded_data_prep_fn
    except Exception as e:
        raise ValueError("Failed to validate model saving and loading from local disk") from e


def validate_data_preparation_function(prediction_function):
    if not callable(prediction_function):
        raise ValueError(
            f"Invalid prediction_function parameter: {prediction_function}. Please specify Python function."
        )


def validate_model_type(model_type):
    if model_type not in {task.value for task in SupportedModelTypes}:
        raise ValueError(
            f"Invalid model_type parameter: {model_type}. "
            + f"Please choose one of {[task.value for task in SupportedModelTypes]}."
        )


def validate_classification_labels(classification_labels: List[str], model_type: SupportedModelTypes):
    if model_type == SupportedModelTypes.CLASSIFICATION:
        if classification_labels is not None and isinstance(classification_labels, Iterable):
            if len(classification_labels) <= 1:
                raise ValueError(
                    f"Invalid classification_labels parameter: {classification_labels}. "
                    f"Please specify more than 1 label."
                )
        else:
            raise ValueError(
                f"Invalid classification_labels parameter: {classification_labels}. "
                f"Please specify valid list of strings."
            )
    if model_type == SupportedModelTypes.REGRESSION and classification_labels is not None:
        warning("'classification_labels' parameter is ignored for regression model")


def validate_features(feature_names=None, validate_df=None):
    if (
            feature_names is not None
            and validate_df is not None
            and not set(feature_names).issubset(set(validate_df.columns))
    ):
        missing_feature_names = set(feature_names) - set(validate_df.columns)
        raise ValueError(
            f"Value mentioned in  feature_names is  not available in validate_df: {missing_feature_names} "
        )


def validate_classification_threshold_label(
        classification_labels, classification_threshold=None
):
    if classification_labels is None:
        raise ValueError(f"Missing classification_labels parameter for classification model.")
    if classification_threshold is not None and not isinstance(
            classification_threshold, (int, float)
    ):
        raise ValueError(
            f"Invalid classification_threshold parameter: {classification_threshold}. Please specify valid number."
        )

    if classification_threshold is not None:
        if classification_threshold != 0.5 and len(classification_labels) != 2:
            raise ValueError(
                f"Invalid classification_threshold parameter: {classification_threshold} value is applicable "
                f"only for binary classification. "
            )


def validate_label_with_target(classification_labels, target_values=None, target_name=None):
    if target_values is not None:
        if not is_string_dtype(target_values):
            print(
                'Hint: "Your target variable values are numeric. '
                "It is recommended to have Human readable string as your target values "
                'to make results more understandable in Giskard."'
            )

        target_values = (
            target_values
            if is_string_dtype(target_values)
            else [str(label) for label in target_values]
        )
        if not set(target_values).issubset(set(classification_labels)):
            invalid_target_values = set(target_values) - set(classification_labels)
            raise ValueError(
                f"Values in {target_name} column are not declared in "
                f"classification_labels parameter: {invalid_target_values}"
            )


def validate_prediction_output(df: pd.DataFrame, model_type, prediction):
    assert len(df) == len(prediction), (
        f"Number of rows ({len(df)}) of dataset provided does not match with the "
        f"number of rows ({len(prediction)}) of prediction_function output"
    )
    if isinstance(prediction, np.ndarray) or isinstance(prediction, list):
        if model_type == SupportedModelTypes.CLASSIFICATION:
            if not any(isinstance(y, (np.floating, float)) for x in prediction for y in x):
                raise ValueError("Model prediction should return float values ")
        if model_type == SupportedModelTypes.REGRESSION:
            if not any(isinstance(x, (np.floating, float)) for x in prediction):
                raise ValueError("Model prediction should return float values ")
    else:
        raise ValueError("Model should return numpy array or a list")


def validate_classification_prediction(classification_labels, prediction):
    if not np.all(np.logical_and(prediction >= 0, prediction <= 1)):
        warning("Output of the prediction_function returns values out of range [0,1]. "
                "The output of Multiclass and Binary classifications should be within the range [0,1]")
    if not np.all(np.isclose(np.sum(prediction, axis=1), 1, atol=0.0000001)):
        warning("Sum of output values of prediction_function is not equal to 1."
                " For Multiclass and Binary classifications, the sum of probabilities should be 1")
    if prediction.shape[1] != len(classification_labels):
        raise ValueError(
            "Prediction output label shape and classification_labels shape do not match"
        )
