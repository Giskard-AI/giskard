import pandas as pd
from typing import Callable, Optional, Iterable, Any

from giskard.models import infer_giskard_cls
from giskard.models.base import CloudpickleBasedModel
from giskard.core.core import ModelType


class Model(CloudpickleBasedModel):
    """
    A class that automatically infer the ML library of the :code:`model` object from the user and provides suitable:

    1. serialization methods (provided by :code:`save_model` and :code:`load_model` methods).

    2. prediction methods (provided by the :code:`model_predict` method).

    Our pre-defined serialization and prediction methods cover the :code:`sklearn`, :code:`catboost`, :code:`pytorch`,
    :code:`tensorflow` and :code:`huggingface` libraries. If none of these libraries are detected, :code:`cloudpickle`
    is used as default for serialization, and you will be asked to provide your own prediction method.

    The user is invited to extend this class:

    - You can choose to override only :code:`model_predict` and take advantage of our internal serialization methods.

    - You can choose to also override :code:`save_model` and :code:`load_model` where you provide your own serialization
    of the :code:`model` object.

    Args:
        model (Union[BaseEstimator, PreTrainedModel, CatBoost, Module]):
            Could be any ML model. The standard model output required for Giskard is:

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
        Union[CloudpickleBasedModel, SKLearnModel, HuggingFaceModel,
        CatboostModel, PyTorchModel, TensorFlowModel]: The wrapped Giskard model.
    """
    should_save_model_class = True

    def __new__(cls, model: Any,
                model_type: ModelType,
                data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                model_postprocessing_function: Callable[[Any], Any] = None,
                name: Optional[str] = None,
                feature_names: Optional[Iterable] = None,
                classification_threshold: Optional[float] = 0.5,
                classification_labels: Optional[Iterable] = None,
                **kwargs
                ):
        """
        Used for dynamical inheritance and returns one of the following class instances:
        :code:`SKLearnModel`, :code:`CatboostModel`, :code:`HuggingFaceModel`, :code:`PyTorchModel`,
        :code:`TensorFlowModel`, depending on the ML library detected in the :code:`model` object.
        If the :code:`model` object provided does not belong to one of these libraries, an instance of
        :code:`CloudpickleBasedModel` is returned in which case:

        1. the default serialization method used will be :code:`cloudpickle`

        2. the user will be asked to provide his own :code:`model_predict` method.

        """

        if not model:
            raise ValueError("The 'Model' class requires a 'model' object. In case you want to create a custom "
                             "class without a 'model' object, please create a subclass of 'CustomModel' instead.")
        else:
            giskard_cls = infer_giskard_cls(model)
            # if the Auto class is overriden (thus != Auto) -> get the methods from the subclass
            # if the Auto class is called (thus == Auto) -> get the methods from the inferred class
            # if giskard_cls == None -> get the methods from CloudpickleBasedModel
            methods_holding_class = cls if cls.__name__ != 'Model' else giskard_cls if giskard_cls else CloudpickleBasedModel
            output_cls = type(cls.__name__, (giskard_cls,), dict(methods_holding_class.__dict__))

            return output_cls(
                model=model,
                model_type=model_type,
                data_preprocessing_function=data_preprocessing_function,
                model_postprocessing_function=model_postprocessing_function,
                name=name,
                feature_names=feature_names,
                classification_threshold=classification_threshold,
                classification_labels=classification_labels,
                **kwargs)
