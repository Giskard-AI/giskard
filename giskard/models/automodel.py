from typing import Any, Callable, Iterable, Optional

import inspect
import logging
from importlib import import_module

import pandas as pd

from ..core.core import ModelType, SupportedModelTypes
from .base.serialization import CloudpickleSerializableModel
from .function import PredictionFunctionModel

logger = logging.getLogger(__name__)

_ml_libraries = {
    ("giskard.models.huggingface", "HuggingFaceModel"): [("transformers", "PreTrainedModel")],
    ("giskard.models.sklearn", "SKLearnModel"): [("sklearn.base", "BaseEstimator")],
    ("giskard.models.langchain", "LangchainModel"): [("langchain.chains.base", "Chain")],
    ("giskard.models.catboost", "CatboostModel"): [("catboost", "CatBoost")],
    ("giskard.models.pytorch", "PyTorchModel"): [("torch.nn", "Module")],
    ("giskard.models.tensorflow", "TensorFlowModel"): [("tensorflow", "Module")],
}


def _get_class(_lib, _class):
    return getattr(import_module(_lib), _class)


def _infer_giskard_cls(model: Any):
    if inspect.isfunction(model) or inspect.ismethod(model):
        return PredictionFunctionModel
    else:
        for _giskard_class, _base_libs in _ml_libraries.items():
            try:
                giskard_cls = _get_class(*_giskard_class)
                base_libs = [_get_class(*_base_lib) for _base_lib in _base_libs]
                if isinstance(model, tuple(base_libs)):
                    return giskard_cls
            except ImportError:
                pass
    return None


class Model(CloudpickleSerializableModel):
    """

    Parameters
    ----------
    model : Any
        Could be any function or ML model. The standard model output required for Giskard is:
        * if classification: an array (nxm) of probabilities corresponding to n data entries
        (rows of pandas.DataFrame)
        and m classification_labels. In the case of binary classification, an array of (nx1) probabilities is
        also accepted.
        Make sure that the probability provided is for the second label provided in classification_labels.
        * if regression or text_generation: an array of predictions corresponding to data entries
        (rows of pandas.DataFrame) and outputs.
    name : Optional[str]
        Name of the model.
    description : Optional[str]
        Description of the model's task. Mandatory for non-langchain text_generation models.
    model_type : ModelType
        The type of the model: regression, classification or text_generation.
    data_preprocessing_function : Optional[Callable[[pd.DataFrame]
        A function that takes a pandas.DataFrame as raw input, applies preprocessing and returns any object
        that could be directly fed to clf. You can also choose to include your preprocessing inside clf,
        in which case no need to provide this argument.
    model_postprocessing_function : Optional[Callable[[Any]
        A function that takes a clf output as input,
        applies postprocessing and returns an object of the same type and shape as the clf output.
    feature_names : Optional[Iterable[str]]
        list of feature names matching the column names in the data that correspond to the features which the model
        trained on. By default, feature_names are all the Dataset columns except from target.
    classification_threshold : float
        represents the classification model threshold, for binary
        classification models.
    classification_labels : Optional[Iterable[str]]
        that represents the classification labels, if model_type is
        classification. Make sure the labels have the same order as the column output of clf.
    **kwargs :
        Additional keyword arguments.

    Returns
    -------


    """

    should_save_model_class = True

    def __new__(
        cls,
        model: Any,
        model_type: ModelType,
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]] = None,
        model_postprocessing_function: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
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
        ``CloudpickleSerializableModel`` is returned in which case:

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
            giskard_cls = _infer_giskard_cls(model)
            # if the Model class is overriden (thus != Model) -> get the methods from the subclass
            # if the Model class is instantiated (thus == Model) -> get the methods from the inferred class
            # if giskard_cls == None -> get the methods from CloudpickleSerializableModel
            is_overriden = cls.__name__ != "Model"  # TODO: Improve this
            if is_overriden:
                if not giskard_cls:
                    giskard_cls = CloudpickleSerializableModel
                # if save_model and load_model are overriden, replace them, if not, these equalities will be identities.
                possibly_overriden_cls = cls
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
            else:  # possibly_overriden_cls = CloudpickleSerializableModel
                raise NotImplementedError(
                    "We could not infer your model library. You have two options:"
                    "\n- Pass a prediction_function to the Model class "
                    '(we will try to serialize it with "cloudpickle").'
                    "\n- Extend the Model class and override "
                    'the abstract "model_predict" method. Upon upload to the Giskard hub, we will try to serialise'
                    'it with "cloudpickle", if that does not work, we will ask you to override the "save_model" and'
                    '"load_model" with your own serialization methods.'
                    "\nWe recommend that you follow our documentation page: "
                    "https://giskard.readthedocs.io/en/latest/getting-started/scan"
                )

            methods = dict(possibly_overriden_cls.__dict__)
            output_cls = type(possibly_overriden_cls.__name__, (giskard_cls,), methods)

            obj = output_cls(
                model=model,
                model_type=SupportedModelTypes(model_type) if isinstance(model_type, str) else model_type,
                data_preprocessing_function=data_preprocessing_function,
                model_postprocessing_function=model_postprocessing_function,
                name=name,
                description=description,
                feature_names=list(feature_names) if feature_names is not None else None,
                classification_threshold=classification_threshold,
                classification_labels=classification_labels,
                **kwargs,
            )

            # Important in order for the load method to be executed consistently
            obj.meta.loader_class = possibly_overriden_cls.__name__
            obj.meta.loader_module = possibly_overriden_cls.__module__

            return obj
