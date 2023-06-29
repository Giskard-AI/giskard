import logging
from abc import ABC
from typing import Callable, Optional, Iterable, Any

import pandas as pd

from giskard.core.core import ModelType
from giskard.models import infer_giskard_cls
from giskard.models.base import CloudpickleBasedModel
from giskard.models.function import PredictionFunctionModel

logger = logging.getLogger(__name__)


class Model(CloudpickleBasedModel, ABC):
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
       - Optional: Our pre-defined serialization and prediction methods cover the ``sklearn``, ``catboost``, ``pytorch``
         , ``tensorflow``, ``huggingface`` and ``langchain`` libraries.
         If none of these libraries are detected, cloudpickle is used as the default for serialization.
         If this fails, we will ask you to also override the ``save_model`` and ``load_model`` methods where you provide your own
         serialization of the model object.

    Args:
        model (Any):
            Could be any function or ML model. The standard model output required for Giskard is:

            * if classification: an array (nxm) of probabilities corresponding to n data entries
              (rows of pandas.DataFrame)
              and m classification_labels. In the case of binary classification, an array of (nx1) probabilities is
              also accepted.
              Make sure that the probability provided is for the second label provided in classification_labels.
            * if regression or text_generation: an array of predictions corresponding to data entries
              (rows of pandas.DataFrame) and outputs.
        name (Optional[str]):
             the name of the model.
        model_type (ModelType):
            The type of the model: regression, classification or text_generation.
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
        Union[CloudpickleBasedModel, SKLearnModel, HuggingFaceModel,
        CatboostModel, PyTorchModel, TensorFlowModel]: The wrapped Giskard model.
    """

    should_save_model_class = True

    def __new__(
        cls,
        model: Any,
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
        Used for dynamical inheritance and returns one of the following class instances:
        ``PredictionFunctionModel``, ``SKLearnModel``, ``CatboostModel``, ``HuggingFaceModel``,
        ``PyTorchModel``, ``TensorFlowModel`` or ``LangchainModel``, depending on the ML library detected in the ``model`` object.
        If the ``model`` object provided does not belong to one of these libraries, an instance of
        ``CloudpickleBasedModel`` is returned in which case:

        1. the default serialization method used will be ``cloudpickle``

        2. you will be asked to provide your own ``model_predict`` method.

        """

        if not model:
            raise ValueError(
                "The 'Model' class cannot be initiated without a `model` argument. "
                "\n`model` can be either a model object (classifier, regressor, etc.) or a prediction function."
                "\nIf a model object is provided, we use a model-tailored serialization method during its upload."
                "\nIf a prediction function is provided, we use cloudpickle to serialize it."
            )
        else:
            giskard_cls = infer_giskard_cls(model)
            # if the Model class is overriden (thus != Model) -> get the methods from the subclass
            # if the Model class is instantiated (thus == Model) -> get the methods from the inferred class
            # if giskard_cls == None -> get the methods from CloudpickleBasedModel
            is_overriden = cls.__name__ != "Model"  # TODO: Improve this
            if is_overriden:
                if not giskard_cls:
                    giskard_cls = CloudpickleBasedModel
                # if save_model and load_model are overriden, replace them, if not, these equalities will be identities.
                possibly_overriden_cls = cls
                possibly_overriden_cls.save_model = giskard_cls.save_model
                possibly_overriden_cls.load_model = giskard_cls.load_model
                possibly_overriden_cls.should_save_model_class = True
            elif giskard_cls:
                input_type = "'prediction_function'" if giskard_cls == PredictionFunctionModel else "'model'"
                logger.info(
                    "Your "
                    + input_type
                    + " is successfully wrapped by Giskard's '"
                    + str(giskard_cls.__name__)
                    + "' wrapper class."
                )
                possibly_overriden_cls = giskard_cls
            else:  # possibly_overriden_cls = CloudpickleBasedModel
                raise NotImplementedError(
                    "We could not infer your model library. You have two options:"
                    "\n- Pass a prediction_function to the Model class "
                    '(we will try to serialize it with "cloudpickle").'
                    "\n- Extend the Model class and override "
                    'the abstract "model_predict" method. Upon upload to the Giskard server, we will try to serialise'
                    'it with "cloudpickle", if that does not work, we will ask you to override the "save_model" and'
                    '"load_model" with your own serialization methods.'
                    "\nWe recommend that you follow our documentation page: "
                    "https://giskard.readthedocs.io/en/latest/getting-started/scan"
                )

            methods = dict(possibly_overriden_cls.__dict__)
            output_cls = type(possibly_overriden_cls.__name__, (giskard_cls,), methods)

            obj = output_cls(
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

            # Important in order for the load method to be executed consistently
            obj.meta.loader_class = possibly_overriden_cls.__name__
            obj.meta.loader_module = possibly_overriden_cls.__module__

            return obj
