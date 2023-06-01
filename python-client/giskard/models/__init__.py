from importlib import import_module
from typing import Callable, Optional, Iterable, Any

import pandas as pd
from rich.console import Console

from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments


def get_class(_lib, _class):
    return getattr(import_module(_lib), _class)


@configured_validate_arguments
def wrap_model(model,
               model_type: ModelType,
               data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
               model_postprocessing_function: Callable[[Any], Any] = None,
               name: Optional[str] = None,
               feature_names: Optional[Iterable] = None,
               classification_threshold: float = 0.5,
               classification_labels: Optional[Iterable] = None,
               **kwargs):
    _libraries = {
        ("giskard.models.huggingface", "HuggingFaceModel"): [("transformers", "PreTrainedModel")],
        ("giskard.models.sklearn", "SKLearnModel"): [("sklearn.base", "BaseEstimator")],
        ("giskard.models.catboost", "CatboostModel"): [("catboost", "CatBoost")],
        ("giskard.models.pytorch", "PyTorchModel"): [("torch.nn", "Module")],
        ("giskard.models.tensorflow", "TensorFlowModel"): [("tensorflow", "Module")]
    }
    console = Console()
    for _giskard_class, _base_libs in _libraries.items():
        try:
            giskard_class = get_class(*_giskard_class)
            base_libs = [get_class(*_base_lib) for _base_lib in _base_libs]
            if isinstance(model, tuple(base_libs)):
                origin_library = _base_libs[0][0].split(".")[0]
                giskard_wrapper = _giskard_class[1]
                console.print("Your model is from '" + origin_library + "', we successfully wrapped it into our own '"
                              + giskard_wrapper + "' wrapper.\nSee our API reference documentation for more details.",
                              style="bold green")
                return giskard_class(model=model,
                                     model_type=model_type,
                                     data_preprocessing_function=data_preprocessing_function,
                                     model_postprocessing_function=model_postprocessing_function,
                                     name=name,
                                     feature_names=feature_names,
                                     classification_threshold=classification_threshold,
                                     classification_labels=classification_labels,
                                     **kwargs)
        except ImportError:
            pass

    raise ValueError(
        'We could not infer your model library. We currently only support models from:'
        '\n- sklearn'
        '\n- pytorch'
        '\n- tensorflow'
        '\n- huggingface'
    )


@configured_validate_arguments
def model_from_sklearn(clf,
                       model_type: ModelType,
                       name: Optional[str] = None,
                       data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                       model_postprocessing_function: Callable[[Any], Any] = None,
                       feature_names: Optional[Iterable] = None,
                       classification_threshold: float = 0.5,
                       classification_labels: Optional[Iterable] = None):
    from giskard import SKLearnModel
    return SKLearnModel(clf,
                        model_type,
                        name,
                        data_preprocessing_function,
                        model_postprocessing_function,
                        feature_names,
                        classification_threshold,
                        classification_labels)


@configured_validate_arguments
def model_from_catboost(clf,
                        model_type: ModelType,
                        name: Optional[str] = None,
                        data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                        model_postprocessing_function: Callable[[Any], Any] = None,
                        feature_names: Optional[Iterable] = None,
                        classification_threshold: float = 0.5,
                        classification_labels: Optional[Iterable] = None):
    from giskard import CatboostModel
    return CatboostModel(clf,
                         model_type,
                         name,
                         data_preprocessing_function,
                         model_postprocessing_function,
                         feature_names,
                         classification_threshold,
                         classification_labels)


@configured_validate_arguments
def model_from_pytorch(clf,
                       model_type: ModelType,
                       torch_dtype=None,
                       device: Optional[str] = "cpu",
                       name: Optional[str] = None,
                       data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                       model_postprocessing_function: Callable[[Any], Any] = None,
                       feature_names: Optional[Iterable] = None,
                       classification_threshold: float = 0.5,
                       classification_labels: Optional[Iterable] = None,
                       iterate_dataset=True):
    from giskard import PyTorchModel
    try:
        import torch
    except ImportError as e:
        raise ImportError("Please install it via 'pip install torch'") from e

    torch_dtype = torch.float32 if not torch_dtype else torch_dtype
    return PyTorchModel(clf,
                        model_type,
                        torch_dtype,
                        device,
                        name,
                        data_preprocessing_function,
                        model_postprocessing_function,
                        feature_names,
                        classification_threshold,
                        classification_labels,
                        iterate_dataset)


@configured_validate_arguments
def model_from_tensorflow(clf,
                          model_type: ModelType,
                          name: Optional[str] = None,
                          data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                          model_postprocessing_function: Callable[[Any], Any] = None,
                          feature_names: Optional[Iterable] = None,
                          classification_threshold: float = 0.5,
                          classification_labels: Optional[Iterable] = None):
    from giskard import TensorFlowModel
    return TensorFlowModel(clf,
                           model_type,
                           name,
                           data_preprocessing_function,
                           model_postprocessing_function,
                           feature_names,
                           classification_threshold,
                           classification_labels)


@configured_validate_arguments
def model_from_huggingface(clf,
                           model_type: ModelType,
                           name: Optional[str] = None,
                           data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                           model_postprocessing_function: Callable[[Any], Any] = None,
                           feature_names: Optional[Iterable] = None,
                           classification_threshold: float = 0.5,
                           classification_labels: Optional[Iterable] = None):
    from giskard import HuggingFaceModel
    return HuggingFaceModel(clf,
                            model_type,
                            name,
                            data_preprocessing_function,
                            model_postprocessing_function,
                            feature_names,
                            classification_threshold,
                            classification_labels)
