from importlib import import_module
from typing import Union, Callable, Optional, Iterable, Any
import pandas as pd
from giskard.core.core import SupportedModelTypes
from giskard.core.validation import validate_args
from giskard.models.sklearn import SKLearnModel
from giskard.models.catboost import CatboostModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.tensorflow import TensorFlowModel
from giskard.models.huggingface import HuggingFaceModel

try:
    import torch
except ImportError as e:
    raise ImportError("Please install it via 'pip install torch'") from e

# format: dict[GiskardModel: list(tuple(module, base_class))]
_libraries = {HuggingFaceModel: [("transformers", "PreTrainedModel")],
              SKLearnModel: [("sklearn.base", "BaseEstimator")],
              CatboostModel: [("catboost", "CatBoost")],
              PyTorchModel: [("torch.nn", "Module")],
              TensorFlowModel: [("tensorflow", "Module")]}


def get_class(_lib, _class):
    return getattr(import_module(_lib), _class)


@validate_args
def model(clf,
          model_type: Union[SupportedModelTypes, str],
          data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
          model_postprocessing_function: Callable[[Any], Any] = None,
          name: Optional[str] = None,
          feature_names: Optional[Iterable] = None,
          classification_threshold: float = 0.5,
          classification_labels: Optional[Iterable] = None,
          **kwargs):
    for giskard_class, _base_libs in _libraries.items():
        try:
            base_libs = [get_class(*_base_lib) for _base_lib in _base_libs]
            if isinstance(clf, tuple(base_libs)):
                return giskard_class(clf=clf,
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


@validate_args
def model_from_sklearn(clf,
                       model_type: Union[SupportedModelTypes, str],
                       name: Optional[str] = None,
                       data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                       model_postprocessing_function: Callable[[Any], Any] = None,
                       feature_names: Optional[Iterable] = None,
                       classification_threshold: float = 0.5,
                       classification_labels: Optional[Iterable] = None):
    return SKLearnModel(clf=clf,
                        model_type=model_type,
                        name=name,
                        data_preprocessing_function=data_preprocessing_function,
                        model_postprocessing_function=model_postprocessing_function,
                        feature_names=feature_names,
                        classification_threshold=classification_threshold,
                        classification_labels=classification_labels)


@validate_args
def model_from_catboost(clf,
                        model_type: Union[SupportedModelTypes, str],
                        name: Optional[str] = None,
                        data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                        model_postprocessing_function: Callable[[Any], Any] = None,
                        feature_names: Optional[Iterable] = None,
                        classification_threshold: float = 0.5,
                        classification_labels: Optional[Iterable] = None):
    return CatboostModel(clf=clf,
                         model_type=model_type,
                         name=name,
                         data_preprocessing_function=data_preprocessing_function,
                         model_postprocessing_function=model_postprocessing_function,
                         feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)


@validate_args
def model_from_pytorch(clf,
                       model_type: Union[SupportedModelTypes, str],
                       torch_dtype: Optional[torch.dtype] = torch.float32,
                       device: Optional[str] = "cpu",
                       name: Optional[str] = None,
                       data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                       model_postprocessing_function: Callable[[Any], Any] = None,
                       feature_names: Optional[Iterable] = None,
                       classification_threshold: float = 0.5,
                       classification_labels: Optional[Iterable] = None,
                       iterate_dataset=True):
    return PyTorchModel(clf=clf,
                        model_type=model_type,
                        torch_dtype=torch_dtype,
                        device=device,
                        name=name,
                        data_preprocessing_function=data_preprocessing_function,
                        model_postprocessing_function=model_postprocessing_function,
                        feature_names=feature_names,
                        classification_threshold=classification_threshold,
                        classification_labels=classification_labels,
                        iterate_dataset=iterate_dataset)


@validate_args
def model_from_tensorflow(clf,
                          model_type: Union[SupportedModelTypes, str],
                          name: Optional[str] = None,
                          data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                          model_postprocessing_function: Callable[[Any], Any] = None,
                          feature_names: Optional[Iterable] = None,
                          classification_threshold: float = 0.5,
                          classification_labels: Optional[Iterable] = None):
    return TensorFlowModel(clf=clf,
                           model_type=model_type,
                           name=name,
                           data_preprocessing_function=data_preprocessing_function,
                           model_postprocessing_function=model_postprocessing_function,
                           feature_names=feature_names,
                           classification_threshold=classification_threshold,
                           classification_labels=classification_labels)


@validate_args
def model_from_huggingface(clf,
                           model_type: Union[SupportedModelTypes, str],
                           name: Optional[str] = None,
                           data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                           model_postprocessing_function: Callable[[Any], Any] = None,
                           feature_names: Optional[Iterable] = None,
                           classification_threshold: float = 0.5,
                           classification_labels: Optional[Iterable] = None):
    return HuggingFaceModel(clf=clf,
                            model_type=model_type,
                            name=name,
                            data_preprocessing_function=data_preprocessing_function,
                            model_postprocessing_function=model_postprocessing_function,
                            feature_names=feature_names,
                            classification_threshold=classification_threshold,
                            classification_labels=classification_labels)
