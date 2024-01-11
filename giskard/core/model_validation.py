from typing import Any, Callable, Iterable, List, Optional, Union

import tempfile

import numpy as np
import pandas as pd
import yaml

from giskard.client.python_utils import warning
from giskard.core.core import ModelMeta, ModelType, SupportedModelTypes
from giskard.core.validation import configured_validate_arguments, validate_is_pandasdataframe
from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel, WrapperModel
from giskard.registry.slicing_function import SlicingFunction

from ..utils import fullname
from ..utils.analytics_collector import analytics, get_dataset_properties, get_model_properties


@configured_validate_arguments
def validate_model(model: BaseModel, validate_ds: Optional[Dataset] = None, print_validation_message: bool = True):
    try:
        _do_validate_model(model, validate_ds)
    except (ValueError, TypeError) as err:
        _track_validation_error(err, model, validate_ds)
        raise err

    # TODO: switch to logger
    if print_validation_message:
        print("Your model is successfully validated.")


def _track_validation_error(err, model, dataset):
    properties = {"error": str(err), "error_class": fullname(err)}
    properties.update(get_model_properties(model))
    properties.update(get_dataset_properties(dataset))

    analytics.track("validate_model:failed", properties)


def _do_validate_model(model: BaseModel, validate_ds: Optional[Dataset] = None):
    model_type = model.model_type

    if isinstance(model, WrapperModel) and model.data_preprocessing_function is not None:
        validate_data_preprocessing_function(model.data_preprocessing_function)

    if isinstance(model, WrapperModel) and model.model_postprocessing_function is not None:
        validate_model_postprocessing_function(model.model_postprocessing_function)

    validate_classification_labels(model.classification_labels, model_type)

    if model.is_classification:
        validate_classification_threshold_label(model.classification_labels, model.classification_threshold)

    assert model.feature_names is None or isinstance(
        model.feature_names, list
    ), "Invalid feature_names parameter. Please provide the feature names as a list."

    if validate_ds is not None:
        validate_is_pandasdataframe(validate_ds.df)
        validate_features(feature_names=model.feature_names, validate_df=validate_ds.df)

        if model.is_regression:
            validate_model_execution(model, validate_ds)
        elif model.is_text_generation:
            validate_model_execution(model, validate_ds, False)
        elif model.is_classification and validate_ds.target is not None:
            target_values = validate_ds.df[validate_ds.target].unique()
            validate_label_with_target(model.name, model.classification_labels, target_values, validate_ds.target)
            validate_model_execution(model, validate_ds)
        else:  # Classification with target = None
            validate_model_execution(model, validate_ds)

        if model.model_type == SupportedModelTypes.CLASSIFICATION and validate_ds.target is not None:
            validate_order_classifcation_labels(model, validate_ds)


@configured_validate_arguments
def validate_model_execution(model: BaseModel, dataset: Dataset, deterministic: bool = True) -> None:
    # testing multiple entries
    validation_size = min(len(dataset), 10)
    validation_ds = dataset.slice(SlicingFunction(lambda x: x.sample(validation_size), row_level=False))
    error_message = (
        "Invalid prediction_function.\nBefore using Giskard, please make sure that "
        "'prediction_function(df[feature_names].head())' does not return an error message."
    )
    try:
        prediction = model.predict(validation_ds)
    except Exception as e:
        features = model.feature_names if model.feature_names is not None else validation_ds.df.columns
        number_of_features = len(features)

        # Some models (mostly sklearn) expect a 1-dimensional ndarray or pd.Series as input in the case they're
        # trained with 1 feature. Here we try to detect in case a user defines their prediction function using
        # model.predict_proba(df) (which would break) instead of model.predict_proba(df.feature)
        one_dimension_case = (
            isinstance(e, IndexError)
            and "index 1 is out of bounds for axis 0 with size 1" in str(e)
            and number_of_features == 1
        )

        if not one_dimension_case:
            raise ValueError(error_message) from e

        feature = features[0]
        one_dimension_error_message = (
            "Your model returned an error when we passed a 'pandas.Dataframe' as input. "
            f"Try to use a one-dimensional input like 'df.{feature}' "
            "inside your prediction function."
        )
        raise ValueError(one_dimension_error_message) from e

    # testing one entry
    validation_size = min(len(dataset), 1)
    validation_ds_1 = dataset.slice(SlicingFunction(lambda x: x.sample(validation_size), row_level=False))
    try:
        model.predict(validation_ds_1)
    except Exception as e:
        raise ValueError(
            error_message + " Hint: Make sure that you are not fitting any preprocessor inside your model or prediction"
            " function."
        ) from e

    if deterministic:
        validate_deterministic_model(model, validation_ds, prediction)
    validate_prediction_output(validation_ds, model.model_type, prediction.raw)
    if model.is_classification:
        validate_classification_prediction(model.classification_labels, prediction.raw)


@configured_validate_arguments
def validate_deterministic_model(model: BaseModel, validate_ds: Dataset, prev_prediction):
    """Asserts if the model is deterministic by asserting previous and current prediction on same data are same"""
    new_prediction = model.predict(validate_ds)

    if not np.allclose(prev_prediction.raw, new_prediction.raw):
        warning(
            "Model is stochastic and not deterministic. Prediction function returns different results"
            "after being invoked for the same data multiple times."
        )


@configured_validate_arguments
def validate_model_loading_and_saving(model: BaseModel):
    """Validates if the model can be serialised and deserialised from local disk"""
    try:
        with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
            model.save(f)

            with open(f + "/giskard-model-meta.yaml") as yaml_f:
                saved_meta = yaml.load(yaml_f, Loader=yaml.Loader)

            meta = ModelMeta(
                name=saved_meta["name"],
                description=saved_meta["description"],
                model_type=SupportedModelTypes[saved_meta["model_type"]],
                feature_names=saved_meta["feature_names"],
                classification_labels=saved_meta["classification_labels"],
                classification_threshold=saved_meta["threshold"],
                loader_module=saved_meta["loader_module"],
                loader_class=saved_meta["loader_class"],
            )

            clazz = BaseModel.determine_model_class(meta, f)

            constructor_params = meta.__dict__
            del constructor_params["loader_module"]
            del constructor_params["loader_class"]

            loaded_model = clazz.load(f, **constructor_params)

            return loaded_model

    except Exception as e:
        raise ValueError("Failed to validate model saving and loading from local disk") from e


@configured_validate_arguments
def validate_data_preprocessing_function(f: Callable[[pd.DataFrame], Any]):
    if not callable(f):
        raise ValueError(f"Invalid data_preprocessing_function parameter: {f}. Please specify Python function.")


@configured_validate_arguments
def validate_model_postprocessing_function(f: Callable[[Any], Any]):
    if not callable(f):
        raise ValueError(f"Invalid model_postprocessing_function parameter: {f}. Please specify Python function.")


@configured_validate_arguments
def validate_model_type(model_type: ModelType):
    if model_type not in {task.value for task in SupportedModelTypes}:
        raise ValueError(
            f"Invalid model_type parameter: {model_type}. "
            + f"Please choose one of {[task.value for task in SupportedModelTypes]}."
        )


@configured_validate_arguments
def validate_classification_labels(classification_labels: Union[np.ndarray, List, None], model_type: ModelType):
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

    if (
        model_type == SupportedModelTypes.REGRESSION or model_type == SupportedModelTypes.TEXT_GENERATION
    ) and classification_labels is not None:
        warning("'classification_labels' parameter is ignored for regression model")


@configured_validate_arguments
def validate_features(feature_names: Optional[List[str]] = None, validate_df: Optional[pd.DataFrame] = None):
    if (
        feature_names is not None
        and validate_df is not None
        and not set(feature_names).issubset(set(validate_df.columns))
    ):
        missing_feature_names = set(feature_names) - set(validate_df.columns)
        raise ValueError(f"Value mentioned in feature_names is not available in validate_df: {missing_feature_names} ")


@configured_validate_arguments
def validate_classification_threshold_label(
    classification_labels: Union[np.ndarray, List, None], classification_threshold: float = None
):
    if classification_labels is None:
        raise ValueError("Missing classification_labels parameter for classification model.")
    if classification_threshold is not None and not isinstance(classification_threshold, (int, float)):
        raise ValueError(
            f"Invalid classification_threshold parameter: {classification_threshold}. Please specify valid number."
        )

    if classification_threshold is not None:
        if not np.isclose(classification_threshold, 0.5, rtol=1e-09, atol=1e-09) and len(classification_labels) != 2:
            raise ValueError(
                f"Invalid classification_threshold parameter: {classification_threshold} value is applicable "
                f"only for binary classification. "
            )


@configured_validate_arguments
def validate_label_with_target(
    model_name: str,
    classification_labels: Union[np.ndarray, List, None],
    target_values: Union[np.ndarray, List, None] = None,
    target_name: str = None,
):
    if target_values is not None:
        to_append = " of the model: " + model_name if model_name else ""
        target_values = list(target_values)
        if not set(target_values).issubset(set(classification_labels)):
            invalid_target_values = set(target_values) - set(classification_labels)
            raise ValueError(
                f'Values {invalid_target_values} in "{target_name}" column are not declared in '
                f"classification_labels parameter {classification_labels}" + to_append
            )


@configured_validate_arguments
def validate_prediction_output(ds: Dataset, model_type: ModelType, prediction):
    assert len(ds.df) == len(prediction), (
        f"Number of rows ({len(ds.df)}) of dataset provided does not match with the "
        f"number of rows ({len(prediction)}) of model.predict output"
    )
    if isinstance(prediction, np.ndarray) or isinstance(prediction, list):
        if model_type == SupportedModelTypes.CLASSIFICATION:
            if not any(isinstance(y, (np.floating, float)) for x in prediction for y in x):
                raise ValueError("Model prediction should return float values ")
        if model_type == SupportedModelTypes.REGRESSION:
            if not any(isinstance(x, (np.floating, float)) for x in prediction):
                raise ValueError("Model prediction should return float values ")
        if model_type == SupportedModelTypes.TEXT_GENERATION:
            if not any(isinstance(x, str) for x in prediction):
                raise ValueError("Model prediction should return string values ")
    else:
        raise ValueError("Model should return numpy array or a list")


@configured_validate_arguments
def validate_classification_prediction(classification_labels: Union[np.ndarray, List, None], prediction):
    if not np.all(np.logical_and(prediction >= 0, prediction <= 1)):
        warning(
            "Output of model.predict returns values out of range [0,1]. "
            "The output of Multiclass and Binary classifications should be within the range [0,1]"
        )
    if not np.all(np.isclose(np.sum(prediction, axis=1), 1, atol=0.0000001)):
        warning(
            "Sum of output values of model.predict is not equal to 1."
            " For Multiclass and Binary classifications, the sum of probabilities should be 1"
        )
    if prediction.shape[1] != len(classification_labels):
        raise ValueError("Prediction output label shape and classification_labels shape do not match")
    if prediction.shape[1] != len(classification_labels):
        raise ValueError("Prediction output label shape and classification_labels shape do not match")


def validate_order_classifcation_labels(model, dataset):
    from sklearn.metrics import balanced_accuracy_score

    y_true = dataset.df[dataset.target]
    y_pred = model.predict(dataset).prediction
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    num_classes = len(model.classification_labels)

    if balanced_accuracy <= 1 / num_classes:
        warning(
            f"The balanced accuracy of your model is very low ({round(balanced_accuracy, 2)}). "
            "Make sure you have not inverted the order of the 'classification_labels' when you created "
            "the Giskard Model."
        )
