"""
To scan, test and debug your model, you need to wrap it into a Giskard Model.
Your model can use any ML library (``sklearn``, ``catboost``, ``pytorch``, ``tensorflow``,
``huggingface`` and ``langchain``) and can be any Python function that respects the right signature.

You can wrap your model in two different ways:

1. Wrap a prediction function that contains all your data pre-processing steps.
   Prediction function is any Python function that takes input as raw pandas dataframe and returns the probabilities
   for each classification labels (classification) or predictions (regression or text_generation).

   Make sure that:

   - ``prediction_function`` encapsulates all the data pre-processing steps (categorical encoding, numerical scaling, etc.).
   - ``prediction_function(df[feature_names])`` does not return an error message.
2. Wrap a model object in addition to a data pre-processing function.
   Providing the model object to Model allows us to automatically infer the ML library of your model object and
   provide a suitable serialization method (provided by ``save_model`` and ``load_model`` methods).

   This requires:

   - Mandatory: Overriding the model_predict method which should take the input as raw pandas dataframe and return
   the probabilities for each classification labels (classification) or predictions (regression or text_generation).
   - Optional: Our pre-defined serialization and prediction methods cover the ``sklearn``, ``catboost``, ``pytorch``,
   ``tensorflow``, ``huggingface`` and ``langchain`` libraries.
   If none of these libraries are detected, cloudpickle is used as the default for serialization.
   If this fails, we will ask you to also override the ``save_model`` and ``load_model`` methods where you provide your own
   serialization of the model object.
"""
import inspect
import logging
from importlib import import_module
from typing import Any, Callable, Iterable, Optional

import pandas as pd

from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.models.function import PredictionFunctionModel

logger = logging.getLogger(__name__)

ml_libraries = {
    ("giskard.models.huggingface", "HuggingFaceModel"): [("transformers", "PreTrainedModel")],
    ("giskard.models.sklearn", "SKLearnModel"): [("sklearn.base", "BaseEstimator")],
    ("giskard.models.langchain", "LangchainModel"): [("langchain.chains.base", "Chain")],
    ("giskard.models.catboost", "CatboostModel"): [("catboost", "CatBoost")],
    ("giskard.models.pytorch", "PyTorchModel"): [("torch.nn", "Module")],
    ("giskard.models.tensorflow", "TensorFlowModel"): [("tensorflow", "Module")],
}


def get_class(_lib, _class):
    return getattr(import_module(_lib), _class)


def infer_giskard_cls(model: Any):
    if inspect.isfunction(model) or inspect.ismethod(model):
        return PredictionFunctionModel
    else:
        for _giskard_class, _base_libs in ml_libraries.items():
            try:
                giskard_cls = get_class(*_giskard_class)
                base_libs = [get_class(*_base_lib) for _base_lib in _base_libs]
                if isinstance(model, tuple(base_libs)):
                    return giskard_cls
            except ImportError:
                pass
    return None


@configured_validate_arguments
def wrap_model(
    model,
    model_type: ModelType,
    data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
    model_postprocessing_function: Callable[[Any], Any] = None,
    name: Optional[str] = None,
    feature_names: Optional[Iterable] = None,
    classification_threshold: Optional[float] = 0.5,
    classification_labels: Optional[Iterable] = None,
    **kwargs,
):
    """
    Wraps a trained model from :code:`sklearn`, :code:`catboost`, :code:`pytorch`, :code:`tensorflow` or
    :code:`huggingface` into a Giskard model.

    Args:
        model (Union[BaseEstimator, PreTrainedModel, CatBoost, Module]):
            Could be any model from :code:`sklearn`, :code:`catboost`, :code:`pytorch`, :code:`tensorflow` or :code:`huggingface`.
            The standard model output required for Giskard is:

            * if classification: an array (nxm) of probabilities corresponding to n data entries (rows of pandas.DataFrame)
                and m classification_labels. In the case of binary classification, an array of (nx1) probabilities is also accepted.
                Make sure that the probability provided is for the first label provided in classification_labels.
            * if regression: an array of predictions corresponding to data entries (rows of pandas.DataFrame) and outputs.
        name (Optional[str]):
             the name of the model.
        model_type (ModelType):
            The type of the model, either regression or classification.
        data_preprocessing_function (Optional[Callable[[pd.DataFrame], Any]]):
            A function that takes a pandas.DataFrame as raw input, applies preprocessing and returns any object
            that could be directly fed to clf. You can also choose to include your preprocessing inside clf,
            in which case no need to provide this argument.
        model_postprocessing_function (Optional[Callable[[Any], Any]]):
            A function that takes a clf output as input,
            applies postprocessing and returns an object of the same type and shape as the clf output.
        feature_names (Optional[Iterable[str]]):
            list of feature names matching the column names in the data that correspond to the features which the model
            trained on. By default, feature_names are all the Dataset columns except from target.
        classification_threshold (float):
            represents the classification model threshold, for binary
            classification models.
        classification_labels (Optional[Iterable[str]]):
            that represents the classification labels, if model_type is
            classification. Make sure the labels have the same order as the column output of clf.
        **kwargs: Additional keyword arguments.

    Returns:
        Union[SKLearnModel, HuggingFaceModel, CatboostModel, PyTorchModel, TensorFlowModel]: The wrapped Giskard model.

    Raises:
        ValueError: If the model library cannot be inferred.
    """
    giskard_cls = infer_giskard_cls(model)
    if giskard_cls:
        logger.info(
            "Your model is successfully wrapped by Giskard's '" + str(giskard_cls.__name__) + "' wrapper class."
        )
        return giskard_cls(
            model=model,
            model_type=model_type,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            name=name,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            **kwargs,
        )
    else:
        raise ValueError(
            "We could not infer your model library. We currently only support functions or models from:"
            "\n- sklearn"
            "\n- catboost"
            "\n- pytorch"
            "\n- tensorflow"
            "\n- huggingface"
            "\n- langchain"
            "\nWe recommend that you create your own wrapper using our documentation page: https://giskard.readthedocs.io/en/latest/guides/custom-wrapper"
        )


@configured_validate_arguments
def model_from_sklearn(
    model,
    model_type: ModelType,
    name: Optional[str] = None,
    data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
    model_postprocessing_function: Callable[[Any], Any] = None,
    feature_names: Optional[Iterable] = None,
    classification_threshold: Optional[float] = 0.5,
    classification_labels: Optional[Iterable] = None,
):
    """
    Factory method that creates an instance of the `SKLearnModel` class.

    Parameters:
        model: Any
            The trained scikit-learn model object to wrap.
        model_type: ModelType
            The type of the model, either `ModelType.CLASSIFICATION` or `ModelType.REGRESSION`.
        name: Optional[str], default=None
            The name of the model.
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]], default=None
            A function that preprocesses the input data before it is fed to the model.
        model_postprocessing_function: Optional[Callable[[Any], Any]], default=None
            A function that post-processes the model's output.
        feature_names: Optional[Iterable], default=None
            A list of feature names.
        classification_threshold: float, default=0.5
            The threshold value used for classification models.
        classification_labels: Optional[Iterable], default=None
            A list of classification labels.

    Returns:
        SKLearnModel
            An instance of the `SKLearnModel` class.
    """
    from giskard.models.sklearn import SKLearnModel

    return SKLearnModel(
        model,
        model_type,
        name,
        data_preprocessing_function,
        model_postprocessing_function,
        feature_names,
        classification_threshold,
        classification_labels,
    )


@configured_validate_arguments
def model_from_catboost(
    model,
    model_type: ModelType,
    name: Optional[str] = None,
    data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
    model_postprocessing_function: Callable[[Any], Any] = None,
    feature_names: Optional[Iterable] = None,
    classification_threshold: Optional[float] = 0.5,
    classification_labels: Optional[Iterable] = None,
):
    """
    Factory method that creates an instance of the `CatboostModel` class.

    Args:
        model (Any): The trained Catboost model object to wrap.
        model_type (ModelType): The type of the model, either `ModelType.CLASSIFICATION` or `ModelType.REGRESSION`.
        name (Optional[str], optional): The name of the model. Defaults to None.
        data_preprocessing_function (Optional[Callable[[pd.DataFrame], Any]], optional):
            A function that preprocesses the input data before it is fed to the model. Defaults to None.
        model_postprocessing_function (Optional[Callable[[Any], Any]], optional):
            A function that post-processes the model's output. Defaults to None.
        feature_names (Optional[Iterable], optional):
            A list of feature names. Defaults to None.
        classification_threshold (float, optional):
            The threshold value used for classification models. Defaults to 0.5.
        classification_labels (Optional[Iterable], optional):
            A list of classification labels. Defaults to None.

    Returns:
        CatboostModel: An instance of the `CatboostModel` class.
    """
    from giskard.models.catboost import CatboostModel

    return CatboostModel(
        model,
        model_type,
        name,
        data_preprocessing_function,
        model_postprocessing_function,
        feature_names,
        classification_threshold,
        classification_labels,
    )


@configured_validate_arguments
def model_from_pytorch(
    model,
    model_type: ModelType,
    torch_dtype=None,
    device: Optional[str] = "cpu",
    name: Optional[str] = None,
    data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
    model_postprocessing_function: Callable[[Any], Any] = None,
    feature_names: Optional[Iterable] = None,
    classification_threshold: Optional[float] = 0.5,
    classification_labels: Optional[Iterable] = None,
    iterate_dataset=True,
):
    """
    Factory method that creates an instance of the `PyTorchModel` class.

    Args:
        model (Any): The trained PyTorch model object to wrap.
        model_type (ModelType): The type of the model, either `ModelType.CLASSIFICATION` or `ModelType.REGRESSION`.
        torch_dtype (Optional[torch.dtype], optional): The data type of the input tensors. Defaults to torch.float32.
        device (Optional[str], optional): The device to run the model on, either "cpu" or "cuda". Defaults to "cpu".
        name (Optional[str], optional): The name of the model. Defaults to None.
        data_preprocessing_function (Optional[Callable[[pd.DataFrame], Any]], optional):
            A function that preprocesses the input data before it is fed to the model. Defaults to None.
        model_postprocessing_function (Optional[Callable[[Any], Any]], optional):
            A function that post-processes the model's output. Defaults to None.
        feature_names (Optional[Iterable], optional):
            A list of feature names. Defaults to None.
        classification_threshold (float, optional):
            The threshold value used for classification models. Defaults to 0.5.
        classification_labels (Optional[Iterable], optional):
            A list of classification labels. Defaults to None.
        iterate_dataset (bool, optional): Whether to iterate over the dataset or feed it to the model at once.
            Defaults to True.

    Returns:
        PyTorchModel: An instance of the `PyTorchModel` class.
    """
    try:
        import torch
    except ImportError as e:
        raise ImportError("Please install it via 'pip install torch'") from e

    torch_dtype = torch.float32 if not torch_dtype else torch_dtype
    from giskard.models.pytorch import PyTorchModel

    return PyTorchModel(
        model,
        model_type,
        torch_dtype,
        device,
        name,
        data_preprocessing_function,
        model_postprocessing_function,
        feature_names,
        classification_threshold,
        classification_labels,
        iterate_dataset,
    )


@configured_validate_arguments
def model_from_tensorflow(
    model,
    model_type: ModelType,
    name: Optional[str] = None,
    data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
    model_postprocessing_function: Callable[[Any], Any] = None,
    feature_names: Optional[Iterable] = None,
    classification_threshold: Optional[float] = 0.5,
    classification_labels: Optional[Iterable] = None,
):
    """
    Factory method that creates an instance of the `TensorFlowModel` class.

    Args:
        model (Any): The trained TensorFlow model object to wrap.
        model_type (ModelType): The type of the model, either `ModelType.CLASSIFICATION` or `ModelType.REGRESSION`.
        name (Optional[str], optional): The name of the model. Defaults to None.
        data_preprocessing_function (Optional[Callable[[pd.DataFrame], Any]], optional):
            A function that preprocesses the input data before it is fed to the model. Defaults to None.
        model_postprocessing_function (Optional[Callable[[Any], Any]], optional):
            A function that post-processes the model's output. Defaults to None.
        feature_names (Optional[Iterable], optional):
            A list of feature names. Defaults to None.
        classification_threshold (float, optional):
            The threshold value used for classification models. Defaults to 0.5.
        classification_labels (Optional[Iterable], optional):
            A list of classification labels. Defaults to None.

    Returns:
        TensorFlowModel: An instance of the `TensorFlowModel` class.
    """
    from giskard.models.tensorflow import TensorFlowModel

    return TensorFlowModel(
        model,
        model_type,
        name,
        data_preprocessing_function,
        model_postprocessing_function,
        feature_names,
        classification_threshold,
        classification_labels,
    )


@configured_validate_arguments
def model_from_huggingface(
    model,
    model_type: ModelType,
    name: Optional[str] = None,
    data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
    model_postprocessing_function: Callable[[Any], Any] = None,
    feature_names: Optional[Iterable] = None,
    classification_threshold: Optional[float] = 0.5,
    classification_labels: Optional[Iterable] = None,
):
    """
    Factory method that creates an instance of the `HuggingFaceModel` class.

    Args:
        model (Any): The trained Hugging Face model object to wrap.
        model_type (ModelType): The type of the model, either `ModelType.CLASSIFICATION` or `ModelType.REGRESSION`.
        name (Optional[str], optional): The name of the model. Defaults to None.
        data_preprocessing_function (Optional[Callable[[pd.DataFrame], Any]], optional):
            A function that preprocesses the input data before it is fed to the model. Defaults to None.
        model_postprocessing_function (Optional[Callable[[Any], Any]], optional):
            A function that post-processes the model's output. Defaults to None.
        feature_names (Optional[Iterable], optional):
            A list of feature names. Defaults to None.
        classification_threshold (float, optional):
            The threshold value used for classification models. Defaults to 0.5.
        classification_labels (Optional[Iterable], optional):
            A list of classification labels. Defaults to None.

    Returns:
        HuggingFaceModel: An instance of the `HuggingFaceModel` class.
    """
    from giskard.models.huggingface import HuggingFaceModel

    return HuggingFaceModel(
        model,
        model_type,
        name,
        data_preprocessing_function,
        model_postprocessing_function,
        feature_names,
        classification_threshold,
        classification_labels,
    )
